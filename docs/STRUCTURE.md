# 파일 구조 안내

채용 공고 목록과 상세 정보를 나누어 수집하고 Google Sheets에 저장하는 업무 코드입니다.

실행 파일 이름은 기존 작업 구간·워크플로와 연결되어 있어 유지했습니다. `docs/`에서 역할과 시작점을 찾을 수 있습니다.

| 구분 | 파일 |
| --- | --- |
| `clear.py` | [clear.py](<../clear.py>) |
| `google_form_package.py` | [google_form_package.py](<../google_form_package.py>) |
| `jora.py` | [jora.py](<../jora.py>) |
| `jora_detail.py` | [jora_detail.py](<../jora_detail.py>) |
| `jora_detail_*.py` | [jora_detail_2.py](<../jora_detail_2.py>), [jora_detail_3.py](<../jora_detail_3.py>), [jora_detail_4.py](<../jora_detail_4.py>), [jora_detail_5.py](<../jora_detail_5.py>) |
| `process_handler.py` | [process_handler.py](<../process_handler.py>) |
| `report.py` | [report.py](<../report.py>) |

`google_form_package.py`는 Google Sheets 인증·브라우저 설정을, `process_handler.py`는 진행 상태 기록을 담당합니다.

## 실행 조건

루트 디렉터리에서 `requirements.txt`를 설치합니다. 브라우저 수집은 Chrome과 호환 드라이버가 필요하고, 시트 기록에는 테스트 시트와 쓰기 권한이 필요합니다. 외부 사이트·시트에 연결하는 실행은 문서 정리 검증 과정에서 수행하지 않았습니다.
