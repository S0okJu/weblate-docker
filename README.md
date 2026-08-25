<a href="https://weblate.org/"><img alt="Weblate" src="https://s.weblate.org/cdn/Logo-Darktext-borders.png" height="80px" /></a>

# weblate-docker: openstack/i18n 언어 관리 도구 테스트 환경

이 저장소는 원래 [WeblateOrg/docker](https://github.com/WeblateOrg/docker)
(Weblate 공식 이미지 빌드 레포)를 fork해서 시작했지만, 이 fork에서는
**이미지를 직접 빌드하지 않고** Docker Hub의 `weblate/weblate:5.4.3.2`를
그대로 받아 쓰기 때문에, 이미지 빌드용 파일(`Dockerfile`, `etc/`,
`patches/` 등)과 업스트림 CI/린트 설정은 전부 정리했습니다. 남아있는 건
아래에서 설명하는 로컬 테스트 환경 하나뿐입니다.

Weblate 자체에 대한 공식 문서는 <https://docs.weblate.org/>,
프로덕션 배포용 공식 docker-compose는
<https://github.com/WeblateOrg/docker-compose>를 참고하세요.

구체적으로는 [gerrit 변경 961371](https://review.opendev.org/c/openstack/i18n/+/961371)에서
제안된 Zanata → Weblate 언어 마이그레이션 스크립트
(`create_languages_weblate.py` / `delete_languages.py`)를 테스트하기 위한
로컬 Weblate 인스턴스를 구성합니다.

## 사전 준비물

이 머신에 미리 설치돼 있어야 하는 건 아래 3개뿐입니다:

- `docker` + `docker compose`
- `tox`
- `git` (바이너리 자체만 — `git-review`는 설치할 필요 없음, `tox -e
  fetch-i18n`이 자체 venv 안에 pip으로 설치해서 사용함)

`wlc`, `requests`, `git-review` 등 파이썬 패키지는 전부 tox가 `.tox/`
밑 격리된 venv에 알아서 설치하므로 따로 pip install 할 필요 없습니다.

## 구성 요소

- `docker-compose.yml` (최상위, 자체 작성) — 공식 `WeblateOrg/docker-compose`
  서브모듈은 쓰지 않습니다. weblate/database/cache 3개 서비스만 있는 단순한
  구성이라, 서브모듈을 쓰면 상대경로 해석이 서브모듈 내부 기준으로
  꼬여서 오히려 관리가 더 어려웠습니다. 대신 이 리포에 필요한 내용만
  담아 직접 작성했습니다:
  - 이미지를 `weblate/weblate:5.4.3.2`로 고정 — **필수**: 961371 패치의
    `WeblateRestService.__init__`이 `WEBLATE_SUPPORTED_VERSION == "5.4"`를
    하드코딩으로 검사해서, 다른 버전에서는 실행 자체를 거부합니다
  - `8080` 포트 노출
  - `settings-override.py`(최상위)를 `/app/data/settings-override.py`에 마운트
- `settings-override.py` (최상위) —
  ([문서](https://docs.weblate.org/en/latest/admin/install/docker.html#overriding-settings-from-the-data-volume)에
  따른 데이터 볼륨 설정 오버라이드):
  - `UPDATE_LANGUAGES = False` — Weblate 내장 언어 목록이 위 도구들로
    생성/삭제한 언어를 덮어쓰지 않도록 함
  - `DEFAULT_LANGUAGE = "en_US"` — Weblate 기본값(`"en"`)은
    `zanata.json`에 없는 코드라, `UPDATE_LANGUAGES=False`와 맞물리면
    언어 상세 페이지가 자기 자신으로 리다이렉트 루프에 빠짐. 실제
    존재하는 코드로 맞춰서 해결
- `tox.ini` + `scripts/` — 컨테이너 라이프사이클과, 두 스크립트가 쓰는
  API 토큰을 관리합니다.
- `i18n/` — 961371 패치가 적용된(`git review -d 961371`) `openstack/i18n`
  로컬 체크아웃. **git에 커밋되지 않습니다** (`.gitignore` 참고) — 이
  Weblate 인스턴스를 대상으로 패치의 스크립트를 돌리기 위한 스크래치
  디렉터리일 뿐입니다.

## tox 환경 목록

| 명령어 | 동작 |
|---|---|
| `tox -e docker-up` | `docker compose up -d` 실행 후 `:8080` 응답까지 대기 |
| `tox -e docker-password` | 컨테이너 로그에서 최초 부팅 시 자동 생성된 관리자 비밀번호를 검색 |
| `tox -e docker-logs` | `weblate` 컨테이너 로그를 follow |
| `tox -e docker-down` | 환경 정지 (`-- -v`를 붙이면 볼륨/데이터까지 삭제) |
| `tox -e fetch-i18n` | `i18n/`이 없으면 클론하고, 961371 패치를 checkout (`git-review`도 tox venv 안에 설치되므로 시스템엔 `git`만 있으면 됨) |
| `tox -e save-token` | Weblate API 토큰을 프롬프트로 입력받아 `.weblate-token`에 저장 (600 권한, gitignore 처리) |
| `tox -e delete-language [-- --apply]` | `i18n/`의 `delete_languages.py` 실행. 기본은 dry-run |
| `tox -e create-language [-- --apply]` | `i18n/`의 `create_languages_weblate.py`를 패치에 포함된 `zanata-plural.json`/`zanata.json`으로 실행. 기본은 dry-run |

## 단계별 가이드

1. **Weblate 기동**

   ```bash
   tox -e docker-up
   ```

2. **초기 관리자 비밀번호 확인** (최초 부팅 시 로그에만 남음)

   ```bash
   tox -e docker-password
   ```

3. **UI에서 로그인 후 API 토큰 발급** — 이 단계는 자동화하지 않고
   의도적으로 사용자가 직접 하도록 남겨둔 부분입니다:

   <http://localhost:8080> 접속 → 2단계에서 확인한 비밀번호로 `admin`
   계정 로그인 → 우측 상단 사용자 메뉴 → **API access** → **Add new
   token**.

4. **토큰 저장** (이후 스크립트들이 재사용):

   ```bash
   tox -e save-token
   ```

   프롬프트가 뜨면 토큰을 붙여넣으세요 (입력값은 화면에 표시되지 않습니다).
   `tox -e save-token -- <TOKEN>`처럼 인자로 넘기지 마세요 — tox가 실행한
   커맨드라인을 그대로 echo하기 때문에 토큰이 터미널 로그/히스토리에
   그대로 남습니다.

5. **패치가 적용된 `openstack/i18n` 체크아웃 준비** (`i18n/`이 아직 없다면, 반복 실행해도 안전):

   ```bash
   tox -e fetch-i18n
   ```

6. **스크립트 실행** (먼저 dry-run, 이상 없으면 apply):

   ```bash
   tox -e delete-language
   tox -e delete-language -- --apply

   tox -e create-language
   tox -e create-language -- --apply
   ```

7. **종료**

   ```bash
   tox -e docker-down          # 데이터 유지한 채 정지
   tox -e docker-down -- -v    # 전부 초기화하고 싶다면
   ```

## 알아두면 좋은 점

- 961371 패치의 `weblate_utils.py`가 `wlc` 패키지를 import하는데,
  `openstack/i18n`의 `requirements.txt`엔 빠져 있습니다 — `delete-language`,
  `create-language` tox 환경은 그 파일 대신 `wlc`를 직접 의존성으로
  설치합니다.
- `WeblateRestService.__init__`은 인자 없이 `wlc.Weblate()`도 생성합니다.
  실행 환경에 따라 `wlc`의 자체 설정 탐색 로직과 충돌할 수 있으니, 문제가
  생기면 알려주세요 — 같이 더 파고들어 고정해보겠습니다.
- 최신 `wlc`(pip 최신 버전, `openstack/i18n`이 버전을 고정 안 해서 그대로
  설치됨)는 `weblate.ini`의 `[weblate] key = ...` 형식을 보안상 거부하고
  `[keys]` 섹션에 **URL 문자열 자체를 옵션 이름으로** 토큰을 넣도록
  바뀌었습니다 (`openstack/i18n`의 README가 설명하는 옛 포맷과 다름).
  `scripts/gen_weblate_ini.py`가 새 포맷에 맞춰 파일을 생성합니다.
