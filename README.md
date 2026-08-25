<a href="https://weblate.org/"><img alt="Weblate" src="https://s.weblate.org/cdn/Logo-Darktext-borders.png" height="80px" /></a>

**Weblate is libre software web-based continuous localization system,
used by over 2500 libre projects and companies in more than 165 countries.**

# Official Docker container for Weblate

[![Website](https://img.shields.io/badge/website-weblate.org-blue.svg)](https://weblate.org/)
[![Translation status](https://hosted.weblate.org/widgets/weblate/-/svg-badge.svg)](https://hosted.weblate.org/engage/weblate/?utm_source=widget)
[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/552/badge)](https://bestpractices.coreinfrastructure.org/projects/552)
[![Documentation](https://readthedocs.org/projects/weblate/badge/)][doc]

## Running Weblate

- [Weblate docker-compose](https://github.com/WeblateOrg/docker-compose)
- [OpenShift](https://docs.weblate.org/en/latest/admin/install/openshift.html)
- [Helm chart for Weblate](https://hub.helm.sh/charts/weblate/weblate)

## Exposed ports

The webserver is running on the port 8080.

## Reverse proxy addresses

When `WEBLATE_IP_PROXY_HEADER=HTTP_X_FORWARDED_FOR` is enabled, configure
`WEBLATE_TRUSTED_PROXY_ADDRESSES` with a whitespace-separated list of the IP
addresses, networks, or hostnames of reverse proxies allowed to supply client
addresses. The built-in nginx uses the resolved address both in its logs and
when forwarding the request to Weblate. With an empty list, it uses the
immediate TCP peer. Because nginx forwards a single normalized address, the
container uses an effective `WEBLATE_IP_PROXY_OFFSET` of `0` in this mode.

## Documentation

Detailed documentation is available in [Weblate documentation][doc].

[doc]: https://docs.weblate.org/en/latest/admin/install/docker.html

---

# 로컬 테스트 환경: openstack/i18n 언어 관리 도구

이 fork는 [gerrit 변경 961371](https://review.opendev.org/c/openstack/i18n/+/961371)에서
제안된 Zanata → Weblate 언어 마이그레이션 스크립트
(`create_languages_weblate.py` / `delete_languages.py`)를 테스트하기 위한
로컬 Weblate 인스턴스를 추가로 구성한 것입니다.

## 사전 준비물

이 머신에 미리 설치돼 있어야 하는 건 아래 3개뿐입니다:

- `docker` + `docker compose`
- `tox`
- `git` (바이너리 자체만 — `git-review`는 설치할 필요 없음, `tox -e
  fetch-i18n`이 자체 venv 안에 pip으로 설치해서 사용함)

`wlc`, `requests`, `git-review` 등 파이썬 패키지는 전부 tox가 `.tox/`
밑 격리된 venv에 알아서 설치하므로 따로 pip install 할 필요 없습니다.

## 공식 저장소 대비 추가된 것

- `docker-compose/settings-override.py` — `UPDATE_LANGUAGES = False`를
  설정해, Weblate 내장 언어 목록이 위 도구들로 생성/삭제한 언어를
  덮어쓰지 않도록 합니다. 컨테이너 내부의 `/app/data/settings-override.py`에
  마운트됩니다
  ([문서](https://docs.weblate.org/en/latest/admin/install/docker.html#overriding-settings-from-the-data-volume)).
- `docker-compose/docker-compose.override.yml` — 이미지를
  `weblate/weblate:5.4.3.2`로 고정하고 `8080` 포트를 노출합니다.
  **이 버전 고정은 필수입니다**: 961371 패치의
  `WeblateRestService.__init__`이 `WEBLATE_SUPPORTED_VERSION == "5.4"`를
  하드코딩으로 검사해서, 다른 버전에서는 실행 자체를 거부합니다.
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
