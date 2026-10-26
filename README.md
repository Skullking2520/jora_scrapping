# Jora 채용 공고 수집·정리

호주 Jora 채용 공고의 목록·상세 정보를 수집하고 Google Sheets에 정리하는 인턴 업무 저장소입니다.

## 수행 배경

Seeka Technology 소프트웨어 개발 인턴 업무로 진행했습니다. 인턴 기간은 2025년 1월–5월이며, 원격근무로 데이터 수집·처리 업무를 수행했습니다.

## 처리 흐름과 시작 위치

| 단계 | 코드 | 역할 |
| --- | --- | --- |
| 목록 수집 | [jora.py](scripts/jora.py) | 공고 목록 수집, 직무명·회사명 조합을 사용한 중복 관리, 진행상태 저장 |
| 상세 수집 | [jora_detail.py](scripts/jora_detail.py) 및 번호별 후속 파일 | 공고 상세 정보 수집·적재 |
| 후처리 | [report.py](scripts/report.py), [clear.py](scripts/clear.py) | 수집 결과 처리와 정리 |
| 시트 연결 | [google_form_package.py](scripts/google_form_package.py) | Google Sheets 연결 |

OpenAI API를 사용하는 정보 구조화 코드가 포함돼 있습니다. 스프레드시트 API 호출에는 재시도와 대기를 적용했습니다.

## 실행 준비

- Python 의존성: `requirements.txt`
- Chrome·ChromeDriver
- 접근 권한이 있는 Google Sheets와 서비스 계정
- API를 사용하는 단계의 `OPENAI_API_KEY`

```bash
python -m pip install -r requirements.txt
```

과거 실행 순서는 [workflow 기록](.github/workflows/scrapping.yaml)에 있습니다. 목록 수집 후 해당 시트를 입력으로 상세 수집을 진행하므로, 단계별 입력·출력 시트를 먼저 맞춰야 합니다.

## 현재 자동화 설정

현재 workflow 파일은 전체가 주석 처리돼 있습니다. 안에 남아 있는 일일 스케줄과 실행 명령은 과거 설정이며, 현재 실행 중인 자동화나 최신 수집 결과를 의미하지 않습니다.

## 코드에서 살펴볼 부분

중복 공고 제외, 재시도, 진행상태 저장·복구, 목록과 상세 수집의 분리를 중심으로 볼 수 있습니다. 번호별 상세 수집 파일은 독립 프로젝트가 아니라 같은 수집 업무를 나눈 구성입니다.

## 인증과 저장 대상

`SERVICE_ACCOUNT_KEY`에는 Google 서비스 계정 JSON을, `SPREADSHEET_URL`에는 본인이 관리하는 테스트 시트 URL을 환경 변수로 설정합니다. `.env.example`은 변수 목록이며 자동으로 로드되지 않습니다. 셸에서 환경 변수를 설정한 후 실행해야 합니다. 기존 업무 시트 주소와 인증 파일 저장을 제거했으므로 새 저장 대상을 먼저 지정해야 합니다.

시트 생성·초기화 함수는 기존 데이터를 지울 수 있습니다. 번호가 붙은 파일을 모두 순서대로 실행하는 방식이 아니며, 분할 구간과 시트 이름을 확인한 파일만 테스트 시트에서 실행합니다.

## 저장소 관리

실행 결과·인증 파일은 버전 관리에서 제외합니다. 공개 소스와 수집 데이터의 공개 범위는 구분하며, 인턴 업무 데이터·시트 접근 권한은 포함하지 않습니다. 현재 파일의 제외 규칙은 이미 추적된 자료나 과거 커밋의 노출을 제거하지 않습니다.

## 저장소 구성

이번 정리에서 실행 코드와 보조 모듈을 `scripts/`로 옮겼습니다. 번호별 작업 구간과 기존 처리 로직은 유지합니다. 의존성과 설정 예시는 루트에 두며, 실행 명령의 기준 경로는 저장소 루트입니다.

설정과 입력 시트를 준비한 뒤 시작 단계만 실행하는 예:

```bash
python scripts/jora.py
```

시트 주소는 `https://docs.google.com/spreadsheets/d/…` 형식이어야 합니다. 누락된 설정·잘못된 URL·유효하지 않은 서비스 계정 JSON은 연결 전에 거부하며, 오류 메시지에 JSON 원문을 넣지 않습니다.

외부 수집 없이 설정·인증 처리를 검사하려면 의존성을 설치한 뒤 `python -m unittest discover -s tests`를 실행합니다.
