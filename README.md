# 길동이 — 길동상사 AI 에이전트

가상의 회사 (주)길동상사의 AI 에이전트 **길동이**를 터미널에서 실행하는 Python 프로젝트입니다.
OpenAI 모델과 LangChain 에이전트를 연결하고, 등록된 도구를 사용해 사용자 질문에 답합니다.

## 제공 기능

- **국가별 현재 날짜·시간 조회**: `get_current_time` 도구로 현지 시간을 확인합니다.
- **분야별 RAG 검색**: 취업규칙, 복리후생, 출장여비, 쇼핑몰 CS 매뉴얼을 검색합니다.
- **Markdown 답변 출력**: Rich로 제목, 목록, 표 등 Markdown 형식을 터미널에 표시합니다.
- **한국어 콘솔 대화**: `You>`로 입력하고 `길동이>`로 답변을 받습니다.
- **대화 맥락 유지**: LangGraph의 `InMemorySaver`로 실행 중 대화 맥락을 유지합니다.
  프로그램을 종료하면 대화 맥락은 사라집니다.
- **입력 기록**: `prompt_toolkit`으로 이전 입력을 탐색하고 `.my_history`에 기록을 저장합니다.
- **도구 기반 응답 규칙**: 시스템 프롬프트에서 도구 결과를 근거로 답하도록 지시합니다.
  처리할 도구가 없으면 “현재 제공된 도구로는 해당 내용을 확인할 수 없습니다.”라고
  안내하도록 설정되어 있습니다. 이 규칙은 프롬프트 기반이며 코드로 강제하지 않습니다.

에이전트에는 소개 도구, 시간 조회 도구와 네 개의 문서 검색 도구가 등록되어 있습니다.
문서 검색은 PostgreSQL/pgvector의 컬렉션별 Retriever를 사용하며,
검색 결과를 바탕으로 메인 에이전트가 답변합니다. 분야별 별도 모델은 호출하지 않습니다.

| 분야 | 도구 | 컬렉션 |
| --- | --- | --- |
| 길동이 소개·사용 방법 | `introduce_gildong` | — |
| 현재 시간 | `get_current_time` | — |
| 취업규칙 | `gd_hr_rules_of_employment` | `rules_of_employment` |
| 복리후생 | `gd_hr_welfare_of_employment` | `welfare_of_employment` |
| 출장여비 | `gd_hr_travel_expenses_of_employment` | `travel_expenses_of_employment` |
| 쇼핑몰 CS | `gd_mall_shopping_cs_manual` | `shopping_cs_manual` |

벡터 저장소의 공통 설정은 `PgVectorStore`에서 관리합니다.
`HumanResourceTool`과 `ShoppingMallCsTool`이 이를 상속해 컬렉션별 검색 도구를 생성합니다.
쇼핑몰 검색 도구는 `ShoppingMallCsTool().as_tool()`로 생성하며,
에이전트에 노출되는 이름은 `gd_mall_shopping_cs_manual`입니다.

소개 도구는 에이전트에 등록된 도구의 이름과 `description`을 읽어 기능을 안내합니다.
`main.py`의 도구 목록에 기능을 추가하면 소개에도 반영되며, 소개 시 다른 도구를 실행하지 않습니다.
시스템 프롬프트는 공통 선택 규칙만 관리하고, 분야별 사용 조건은 각 도구의
`description`에 작성합니다. 도구를 추가할 때 프롬프트에 별도 목록을 추가할 필요가 없습니다.

## 실행 환경

- Python 3.14 이상 (개발 컨테이너: 3.14.7)
- uv
- OpenAI API 키
- 문서 저장·검색에 사용할 PostgreSQL + pgvector
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

`PG_*` 변수는 PDF 적재와 에이전트의 문서 검색에 사용됩니다.
컨테이너 밖에서 Compose DB에 접속할 때는 `PG_HOST=localhost`, `PG_PORT=15432`로 설정하세요.
대화 모델은 `OPENAI_MODEL`로 설정하며, 임베딩은 적재·검색 모두 `OpenAIEmbeddings()` 기본 모델을 사용합니다.
임베딩 모델을 변경한다면 양쪽 설정을 맞추고 문서를 다시 임베딩해야 합니다.
`.env`는 Git에서 제외되어 있습니다.

## 로컬 실행

프로젝트 루트에서 의존성을 설치합니다. DB를 준비하고 아래 PDF 문서 적재를 완료한 후 에이전트를 실행하세요.

```bash
uv sync
uv run agent
```

위 명령은 Linux/macOS 및 컨테이너의 셸 기준입니다. Windows PowerShell에서는
다음과 같이 실행합니다.

```powershell
uv run agent
```

`uv_build`로 `src/agent` 패키지를 설치하고, `agent.main:main` 진입점으로
`agent` 명령을 생성합니다. `uv run agent`는 실행 전에 의존성과 프로젝트를 동기화합니다.

## Dev Container 실행

1. `.env`를 준비하고 API 키를 입력합니다.
2. VS Code에서 프로젝트 폴더를 엽니다.
3. 명령 팔레트에서 `Dev Containers: Reopen Folder in Container`를 실행합니다.
4. 컨테이너 터미널에서 아래 PDF 문서 적재를 완료한 후 에이전트를 실행합니다.

```bash
uv run agent
```

컨테이너 시작 시 `uv lock`과 `uv sync --no-dev`가 실행되며, Python 환경은
`/opt/venv`에 생성됩니다. Compose는 `app`과 `db` 서비스를 함께 실행합니다.

VS Code 없이 Docker Compose로 실행할 수도 있습니다.

```bash
docker compose up -d --build
docker compose exec app uv run agent
```

| 서비스 | 컨테이너 포트 | 호스트 포트 | 용도                                                 |
| ------ | ------------- | ----------- | ---------------------------------------------------- |
| `app`  | `8000`        | `18000`     | 앱 개발용 포트 매핑 (현재 HTTP 서버는 실행하지 않음) |
| `db`   | `5432`        | `15432`     | PostgreSQL 18 + pgvector                             |

DB 데이터는 `postgres-gildong-sangsa` 볼륨에 저장됩니다.

## PDF 문서 적재

`resources/`에 아래 PDF 파일을 준비합니다.

| 파일 | 저장 컬렉션 |
| --- | --- |
| `1_취업규칙_길동상사.pdf` | `rules_of_employment` |
| `2_복리후생_규정_길동상사.pdf` | `welfare_of_employment` |
| `3_출장여비_규정_길동상사.pdf` | `travel_expenses_of_employment` |
| `4_쇼핑몰_CS_실무_매뉴얼_길동상사.pdf` | `shopping_cs_manual` |

프로젝트 루트에서 실행합니다. DB가 실행 중이어야 합니다.

```bash
uv run python src/doc-importer/main.py
```

Compose 환경에서는 다음 명령을 사용합니다.

```bash
docker compose exec app uv run python src/doc-importer/main.py
```

적재 과정은 PDF 로드 → 토큰 기준 청크 분할 → OpenAI 임베딩 생성 → 컬렉션별 저장입니다.
기본 분할 설정은 `chunk_size=1000`, `chunk_overlap=200`, `encoding_name="cl100k_base"`입니다.
파일별로 `1 of 4 완료`와 같은 진행 상황이 표시됩니다.
현재 적재 코드는 중복 제거 없이 문서를 추가하므로, 같은 파일을 다시 실행하면 중복 저장될 수 있습니다.

검색 도구는 `similarity` 방식으로 관련 청크를 최대 4개 반환하며,
각 청크를 출처(`metadata["source"]`)와 본문이 포함된 `<document>` 형식으로 전달합니다.
PDF 적재 시 `source`가 누락되면 파일명을 넣습니다. 기존 저장 문서에 출처가 없으면
검색 결과에 `출처 정보 없음`을 표시하며, 원본 DB 문서는 변경하지 않습니다. 검색 결과에 답변 근거가 있는지는 에이전트가 판단합니다.

## 사용 방법

실행 후 자연어로 질문합니다.

```text
You> 길동이는 무엇을 할 수 있어?
You> 한국은 지금 몇 시야?
You> 일본의 현재 날짜와 시간을 알려줘
You> America/New_York의 현재 시간을 알려줘
You> 연차휴가 사용 기준을 알려줘
You> 복리후생 지원 대상과 신청 방법을 알려줘
You> 출장 숙박비 정산 기준은 무엇이야?
You> 쇼핑몰 반품 요청은 어떻게 처리해야 해?
```

시간 도구는 `CurrentTimeTool` 클래스로 구현하며, `as_tool()`이 반환하는
`get_current_time` 도구를 에이전트에 등록합니다. Python 코드에서는
`CurrentTimeTool().get_current_time("한국")`으로 직접 사용할 수 있습니다.

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
├── .agents/skills/                  # pr, code-review, issue 작업 스킬
├── .github/                        # PR 및 버그·기능 요청 템플릿
├── AGENTS.md                       # 저장소 전체의 AI 작업 지침
├── .env.example                    # 환경 변수 예제
├── .pre-commit-config.yaml         # 코드 및 커밋 메시지 검사
├── .vscode/settings.json           # 포맷터 및 커밋 작성 설정
├── Dockerfile                      # Python + uv 개발 이미지
├── docker-compose.yml              # 앱 및 DB 서비스
├── pyproject.toml                  # 의존성 및 프로젝트 설정
├── uv.lock                         # 의존성 잠금 파일
├── resources/                      # 적재할 PDF 문서
└── src/
    ├── doc-importer/main.py        # PDF 분할·임베딩·DB 적재
    └── agent/
        ├── main.py                # 콘솔 입력, Markdown 출력 및 에이전트 구성
        ├── __init__.py            # 설치 가능한 agent 패키지
        ├── store/
        │   ├── pg_vector_store.py # DB 연결과 벡터 저장소 기반 클래스
        │   └── source_retriever.py # 검색 결과 출처 보정
        └── tools/
            ├── __init__.py        # 도구 내보내기
            ├── current_time_tool.py    # 현재 시간 조회
            ├── introduction_tool.py    # 등록된 도구 기반 소개
            ├── human_resource_tool.py  # 취업규칙·복리후생·출장여비 검색
            └── shopping_mall_cs_tool.py # 쇼핑몰 CS 검색
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

## AI 작업 지침과 스킬

[AGENTS.md](AGENTS.md)는 저장소 전체에 적용되는 AI 작업 지침입니다.
프로젝트 구조, 코드·docstring 작성 규칙, RAG 도구 연결과 임베딩 일치,
검증 방법 및 GitHub 작업 범위를 정의합니다. 개발 방식이 변경되면 이 지침도 함께 갱신합니다.

반복 작업의 절차는 `.agents/skills/`에 프로젝트 스킬로 관리합니다.

| 스킬 | 역할 | 파일 |
| --- | --- | --- |
| `pr` | 변경 검토, PR 제목·본문 작성, 요청받은 PR 생성·수정 | [SKILL.md](.agents/skills/pr/SKILL.md) |
| `code-review` | 버그, 회귀 위험, RAG 근거·출처 처리와 DB 설정 검토 | [SKILL.md](.agents/skills/code-review/SKILL.md) |
| `issue` | 버그·기능 요청 정리, 요청받은 이슈 생성·수정 | [SKILL.md](.agents/skills/issue/SKILL.md) |

프로젝트 스킬을 지원하는 AI 도구에서 다음과 같이 요청할 수 있습니다.

```text
$pr 현재 브랜치 변경으로 PR 제목과 본문을 작성해줘
$code-review 현재 변경사항의 버그와 회귀 위험을 검토해줘
$issue 문서 검색 오류를 버그 이슈 문안으로 정리해줘
```

스킬은 작업 절차를 정의합니다. 실제 GitHub 작업에는 인증된 `gh` CLI 또는
연결된 GitHub 도구와 저장소 권한이 필요합니다. 문안 작성과 실제 생성은 요청 범위에 따라 구분합니다.

## GitHub 템플릿

| 템플릿 | 작성 항목 | 파일 |
| --- | --- | --- |
| PR | 변경 목적, 주요 변경, 관련 이슈, 검증 결과, 영향·제한 사항 | [PR 템플릿](.github/pull_request_template.md) |
| 버그 보고 | 문제 설명, 재현 방법, 기대·실제 동작, 환경, 로그, RAG 관련 정보 | [버그 템플릿](.github/ISSUE_TEMPLATE/bug_report.md) |
| 기능 요청 | 해결할 문제, 원하는 동작, 작업 범위, 완료 조건, RAG 요구사항 | [기능 요청 템플릿](.github/ISSUE_TEMPLATE/feature_request.md) |

템플릿이 기본 브랜치에 반영되면 GitHub에서 새 PR이나 이슈를 작성할 때 사용할 수 있습니다.
해당하는 항목만 작성하고 불필요한 항목은 삭제합니다. 검증 결과에는 실제 DB/OpenAI
호출과 모의 검증을 구분하며, API 키·토큰·비밀번호와 개인정보는 포함하지 않습니다.

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

## 인사 검색 도구 구성

`src/agent/tools/human_resource_tool.py`의 `HumanResourceTool`에서 취업규칙,
복리후생, 출장여비 검색을 관리합니다. `as_tools()`로 세 개의 도구를 생성해
에이전트에 등록합니다. 분야별 컬렉션과 기존 도구 이름은 유지합니다.
공통 검색 구현은 한 클래스에서 공유하면서 분야별 도구 이름과 설명은 구분합니다.

에이전트의 도구 목록은 다음 형태로 구성합니다.

```python
tools = [
    CurrentTimeTool().as_tool(),
    *HumanResourceTool().as_tools(),
    ShoppingMallCsTool().as_tool(),
]
tools.append(IntroductionTool(tools).as_tool())
```

새 도구는 이 목록에 등록하고 `tools/__init__.py`에서 내보냅니다.
기능 소개는 등록된 도구에서 자동 생성되고, 시스템 프롬프트는 도구 설명과
입력 스키마를 참고하도록 구성되어 있어 분야별 목록을 별도로 수정할 필요가 없습니다.
