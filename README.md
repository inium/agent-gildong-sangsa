# 길동이 — 길동상사 AI 에이전트

가상의 회사 (주)길동상사의 AI 에이전트 **길동이**를 터미널에서 실행하는 Python 프로젝트입니다.
OpenAI 모델과 LangChain 에이전트를 연결하고, 등록된 도구를 사용해 사용자 질문에 답합니다.

## 제공 기능

- **국가별 현재 날짜·시간 조회**: `get_current_time` 도구로 현지 시간을 확인합니다.
- **한국어 콘솔 대화**: `You>`로 입력하고 `길동이>`로 답변을 받습니다.
- **대화 맥락 유지**: LangGraph의 `InMemorySaver`로 실행 중 대화 맥락을 유지합니다.
  프로그램을 종료하면 대화 맥락은 사라집니다.
- **입력 기록**: `prompt_toolkit`으로 이전 입력을 탐색하고 `.my_history`에 기록을 저장합니다.
- **도구 기반 응답 규칙**: 시스템 프롬프트에서 도구 결과를 근거로 답하도록 지시합니다.
  처리할 도구가 없으면 “현재 제공된 도구로는 해당 내용을 확인할 수 없습니다.”라고
  안내하도록 설정되어 있습니다. 이 규칙은 프롬프트 기반이며 코드로 강제하지 않습니다.

현재 에이전트에 등록된 도구는 시간 조회 도구 하나입니다.
PostgreSQL/pgvector 개발 환경은 포함되어 있지만, 사내 문서 검색이나 DB 조회는
이 버전의 에이전트에 연결되어 있지 않습니다.

## 실행 환경

- Python 3.14 이상 (개발 컨테이너: 3.14.7)
- uv
- OpenAI API 키
- 컨테이너 개발 시 Docker Compose와 VS Code Dev Containers 확장

## 환경 변수

프로젝트 루트에서 예제 파일을 복사합니다.

```bash
cp .env.example .env
```

`.env`의 `OPENAI_API_KEY`에 실제 API 키를 입력합니다.

| 변수             | 용도                  | 예제 파일의 기본값        |
| ---------------- | --------------------- | ------------------------- |
| `OPENAI_API_KEY` | OpenAI API 인증 키    | 직접 입력                 |
| `OPENAI_MODEL`   | 사용할 모델 이름      | `gpt-4o-mini`             |
| `PG_HOST`        | PostgreSQL 호스트     | `agent-gildong-sangsa-db` |
| `PG_PORT`        | PostgreSQL 포트       | `5432`                    |
| `PG_DATABASE`    | 데이터베이스 이름     | `gildong-sangsa-admin`    |
| `PG_USERNAME`    | 데이터베이스 사용자   | `root`                    |
| `PG_PASSWORD`    | 데이터베이스 비밀번호 | `password`                |

`PG_*` 변수는 DB 개발 환경용입니다. 현재 콘솔 에이전트는 DB를 조회하지 않습니다.
`.env`는 Git에서 제외되어 있습니다.

## 로컬 실행

프로젝트 루트에서 의존성을 설치하고 에이전트를 실행합니다.

```bash
uv sync
PYTHONPATH=src uv run python -m agent.main
```

위 명령은 Linux/macOS 및 컨테이너의 셸 기준입니다. Windows PowerShell에서는
다음과 같이 실행합니다.

```powershell
$env:PYTHONPATH = "src"
uv run python -m agent.main
```

현재 `pyproject.toml`에는 빌드 백엔드 선언이 없고 `agent` 실행 진입점이
`agent:main:main`으로 지정되어 있으므로, 여기서는 소스 경로를 지정해 모듈을 직접 실행합니다.

## Dev Container 실행

1. `.env`를 준비하고 API 키를 입력합니다.
2. VS Code에서 프로젝트 폴더를 엽니다.
3. 명령 팔레트에서 `Dev Containers: Reopen Folder in Container`를 실행합니다.
4. 컨테이너 터미널에서 실행합니다.

```bash
PYTHONPATH=src uv run python -m agent.main
```

컨테이너 시작 시 `uv lock`과 `uv sync --no-dev`가 실행되며, Python 환경은
`/opt/venv`에 생성됩니다. Compose는 `app`과 `db` 서비스를 함께 실행합니다.

VS Code 없이 Docker Compose로 실행할 수도 있습니다.

```bash
docker compose up -d --build
docker compose exec app sh -c 'PYTHONPATH=src uv run python -m agent.main'
```

| 서비스 | 컨테이너 포트 | 호스트 포트 | 용도                                                 |
| ------ | ------------- | ----------- | ---------------------------------------------------- |
| `app`  | `8000`        | `18000`     | 앱 개발용 포트 매핑 (현재 HTTP 서버는 실행하지 않음) |
| `db`   | `5432`        | `15432`     | PostgreSQL 18 + pgvector                             |

DB 데이터는 `postgres-gildong-sangsa` 볼륨에 저장됩니다.

## 사용 방법

실행 후 자연어로 질문합니다.

```text
You> 한국은 지금 몇 시야?
You> 일본의 현재 날짜와 시간을 알려줘
You> America/New_York의 현재 시간을 알려줘
```

시간 도구는 한국, 일본, 중국, 인도, 영국, 독일, 싱가포르의 국가명과 코드를 지원합니다.
다른 지역은 `Europe/Paris`처럼 IANA 시간대를 지정할 수 있습니다.
미국처럼 시간대가 여러 개인 국가는 `America/New_York`와 같이 지역을 지정합니다.
결과에는 날짜, 시간, 시간대 약어와 UTC 오프셋이 포함됩니다.

- 이전 입력 탐색: ↑ / ↓
- 종료: `exit`, `quit`, Ctrl+C 또는 빈 입력에서 Ctrl+D

## 프로젝트 구조

```text
.
├── .devcontainer/devcontainer.json  # VS Code 개발 컨테이너 설정
├── .env.example                    # 환경 변수 예제
├── .pre-commit-config.yaml         # 코드 및 커밋 메시지 검사
├── .vscode/settings.json           # 포맷터 및 커밋 작성 설정
├── Dockerfile                      # Python + uv 개발 이미지
├── docker-compose.yml              # 앱 및 DB 서비스
├── pyproject.toml                  # 의존성 및 프로젝트 설정
├── uv.lock                         # 의존성 잠금 파일
└── src/agent/
    ├── main.py                     # 콘솔 입력 및 에이전트 구성
    └── tools/datetime.py           # 국가별 현재 시간 조회 도구
```

## 개발 검사

Git 훅을 설치합니다.

```bash
uv run pre-commit install
```

설정에 따라 `pre-commit`과 `commit-msg` 훅이 설치됩니다.
전체 파일 검사는 다음과 같이 실행합니다.

```bash
uv run pre-commit run --all-files
```

검사 항목은 YAML/TOML 구문, 병합 충돌 표시, 파일 끝 개행, 줄 끝 공백,
Black 포맷과 Conventional Commits 메시지 형식입니다.

## 커밋 규칙

Conventional Commits와 gitmoji를 함께 사용합니다. 이모지는 설명의 맨 앞에 넣습니다.

```text
<type>(<scope>): <gitmoji> <설명>
```

scope는 선택 사항이며, 프로젝트에서는 `설정`, `Agent`, `패키지`를 사용합니다.

| 타입       | gitmoji | 용도                          |
| ---------- | ------- | ----------------------------- |
| `feat`     | ✨      | 새로운 기능 추가              |
| `fix`      | 🐛      | 버그 수정                     |
| `docs`     | 📝      | 문서 추가·수정                |
| `style`    | 🎨      | 동작 변경 없는 코드 포맷 정리 |
| `refactor` | ♻️      | 기능 변경 없는 코드 구조 개선 |
| `perf`     | ⚡️      | 성능 개선                     |
| `test`     | ✅      | 테스트 추가·수정              |
| `build`    | 📦      | 빌드·패키징 관련 변경         |
| `ci`       | 👷      | CI 설정·스크립트 변경         |
| `chore`    | 🔧      | 설정 및 유지보수              |
| `revert`   | ⏪️      | 이전 변경 되돌리기            |

의존성 변경에는 작업에 따라 ➕(추가), ⬆️(업데이트), ➖(제거)를 사용합니다.

```text
feat(Agent): ✨ 국가별 현재 시간 조회 기능 추가
fix(Agent): 🐛 종료 명령 처리 오류 수정
build(패키지): ➕ prompt-toolkit 의존성 추가
build(패키지): ⬆️ langchain 버전 업데이트
build(패키지): ➖ 사용하지 않는 의존성 제거
chore(설정): 🔧 pre-commit 검사 설정 변경
```

기존 호환성을 깨는 변경에는 `!`와 💥를 사용하고, 본문 아래에 변경 내용과
이전 방법에서 새 방법으로 전환하는 방법을 `BREAKING CHANGE:`로 설명합니다.

```text
feat(Agent)!: 💥 시간 조회 도구의 필수 인자 변경

BREAKING CHANGE: country 인자가 필수입니다. 기존 호출에 country를 추가하세요.
```

VS Code 명령 팔레트에서 `Conventional Commits`를 실행하면 타입, scope,
gitmoji를 선택해 커밋 메시지를 작성할 수 있습니다. 프로젝트 설정은 실제 이모지를
사용하도록 지정되어 있으며, 타입별 이모지는 위 표를 기준으로 선택합니다.

기존 `commit-msg` 훅은 Conventional Commits 형식을 검사합니다.
gitmoji의 포함 여부와 타입별 매핑은 문서 규칙이며 별도로 강제하지 않습니다.

참고: [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/),
[gitmoji](https://gitmoji.dev/),
[VS Code 확장 설정](https://github.com/vivaxy/vscode-conventional-commits#extension-configuration).
