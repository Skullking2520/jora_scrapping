# Jora 채용 공고 수집·정리

호주 Jora 채용 공고의 목록·상세 정보를 수집하고 Google Sheets에 정리하는 인턴 업무 저장소입니다.

## 수행 배경

Seeka Technology 소프트웨어 개발 인턴 업무로 진행했습니다. 인턴 기간은 2025년 1월–5월이며, 원격근무로 데이터 수집·처리 업무를 수행했습니다.

## 처리 흐름과 시작 위치

| 단계 | 코드 | 역할 |
| --- | --- | --- |
| 목록 수집 | [jora.py](jora.py) | 공고 목록 수집, 직무명·회사명 조합을 사용한 중복 관리, 진행상태 저장 |
| 상세 수집 | [jora_detail.py](jora_detail.py) 및 번호별 후속 파일 | 공고 상세 정보 수집·적재 |
| 후처리 | [report.py](report.py), [clear.py](clear.py) | 수집 결과 처리와 정리 |
| 시트 연결 | [google_form_package.py](google_form_package.py) | Google Sheets 연결 |

OpenAI API를 사용하는 정보 구조화 코드가 포함돼 있습니다. 스프레드시트 API 호출에는 재시도와 대기를 적용했습니다.

## 실행 준비

- Python 의존성: `requirements.txt`
- Chrome·ChromeDriver
- 접근 권한이 있는 Google Sheets와 서비스 계정
- API를 사용하는 단계의 `OPENAI_API_KEY`

```bash
python -m pip install -r requirements.txt
```

기존 실행 순서와 인증 파일 생성 방식은 [workflow 기록](.github/workflows/scrapping.yaml)에 있습니다. 목록 수집 후 해당 시트를 입력으로 상세 수집을 진행하므로, 단계별 입력·출력 시트를 먼저 맞춰야 합니다.

## 현재 자동화 설정

현재 workflow 파일은 전체가 주석 처리돼 있습니다. 안에 남아 있는 일일 스케줄과 실행 명령은 과거 설정이며, 현재 실행 중인 자동화나 최신 수집 결과를 의미하지 않습니다.

## 코드에서 살펴볼 부분

중복 공고 제외, 재시도, 진행상태 저장·복구, 목록과 상세 수집의 분리를 중심으로 볼 수 있습니다. 번호별 상세 수집 파일은 독립 프로젝트가 아니라 같은 수집 업무를 나눈 구성입니다.
