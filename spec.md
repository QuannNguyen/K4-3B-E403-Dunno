# Template AI Spec *(spec.md — commit trước hạn chốt spec: 21:00 18/9, tại CP4 · quality bar chốt từ thời điểm nộp)*

> Cấu trúc phủ đúng "SPEC 8 phần" của chương trình: Bằng chứng (§1-§2) · Lát cắt (§4) · Canvas (đính kèm CP1) · Augment/Automate (§4) · 4 đường đi của trải nghiệm (§6) · Kiểu lỗi (§5) · Kiểm thử (§7) · Phân công (§8). Hướng dẫn viết từng mục: `02-guide.md`.

```markdown
# AI SPEC — Knowledge-to-Lesson · Nhóm 3B · Zone 2
Hướng: [x] A — VLearn  [ ] B — Trợ lý Học viên  [ ] C — Làn mở
Loại: [x] Tối ưu tính năng có sẵn  [ ] Tính năng mới

## §1. User & Job
- Job executor + workflow (đính kèm worksheet JTBD / ảnh sơ đồ):
  - Người dùng chính: học viên đang học trên VLearn, vừa làm xong quiz/kiểm tra nhanh của một chương và nhận ra mình sai ở câu nâng cao.
  - Workflow: học viên làm bài chẩn đoán → hệ thống ánh xạ câu sai vào concept → xác định concept nền bị thiếu → đề xuất lộ trình(slide/tiết cần ôn) → học viên xem lại nội dung mục tiêu → tiếp tục học/chọn học tiếp.
  - Mục tiêu của từng bước là giảm thời gian “lội ngược bài cũ” và tăng khả năng học tiếp đúng nhịp.

- Core JTBD (không tên sản phẩm/AI trong câu):
  - Học viên cần biết mình đang thiếu concept nào ở trước đó, cần đọc lại phần nào và nên ôn theo thứ tự nào để không tiếp tục sai ở bài sau.

- Problem statement (KHÔNG chữ AI):
  - Học viên đang tự học nhưng không biết mình thiếu kiến thức tiên quyết ở đâu; họ phải tự rà lại 40–50 slide cũ, hoặc học tiếp mà chưa giải quyết lỗ hổng, dẫn đến lặp lại lỗi và mất nhịp học.

- Evidence (chuẩn A và/hoặc B — log đầy đủ trong repo):
  - Số liệu mining từ pack dữ liệu VLearn (không dùng khảo sát):
    - `data/vlearn-pack/README.md` ghi nhận tổng cộng 13.494 lượt hỏi-đáp học viên × AI tutor trong khoảng 22/07 → 15/09/2026.
    - `move_used` chiếm phần lớn ở giá trị `review_concept`, cho thấy nhiều học viên đang trong trạng thái “tra lại khái niệm / ôn lại kiến thức mà họ đã mất gốc”.
    - `has_citation = False` ở 3.781 lượt, cho thấy nhiều câu hỏi không có căn cứ rõ trong tài liệu, khiến học viên gặp khó khăn khi cần tìm lại slide hoặc kiến thức nền từ đầu.
    - 90% hành vi học sinh dùng `review_concept` và rất ít `ask_probing_question`, phản ánh xu hướng học viên cần được dẫn lại nội dung nền hơn là được hỏi ngược.
  - ≥5 quote/ví dụ nguyên văn + nguồn (từ `data/vlearn-pack/chatlog/tutor_turns.csv`):
    1. “Tôi đang bị mất gốc, hãy chỉ ra phần kiến thức tiên quyết cần biết.” — nguồn: `turn_id=T01524`, `student=S1405`, `lecture=day03-tu-chatbot-den-agentic-agent-react`
    2. “mình bị hổng kiến thức nền, phần gradient ko hiểu, nghĩa là phần đạo hàm hàm nhiều biến mình ko hiểu. Dạy mình chi tiết như nội dung trong giáo trình giải tích nhé” — nguồn: `turn_id=T04903`, `student=S1559`, `lecture=Day13-monitoring-logging-observability`
    3. “tôi đã điều hướng bạn sang Day 1, bây giờ giúp tôi ôn lại kiến thức Day 1 đi” — nguồn: `turn_id=T04273`, `student=S0815`, `lecture=Day10-data-pipeline-observability`
    4. “bạn giúp tôi ôn lại bài 1” — nguồn: `turn_id=T04272`, `student=S0815`, `lecture=Day10-data-pipeline-observability`
    5. “Tôi cần ôn lại kiến thức phần này” — nguồn: `turn_id=T04905`, `student=S0554`, `lecture=Day12-cloud-services-and-deployment`
    6. “đây là kiến thức nền tảng... tôi cần được dạy tiếng Việt bài bản” — nguồn: `turn_id=T04904`, `student=S1559`, `lecture=Day13-monitoring-logging-observability`

## §2. Impact & quyết định chọn
- Bảng impact ≥3 ứng viên (bao nhiêu người · tần suất · tốn gì mỗi lần · khả thi):

| Ứng viên | Số người | Tần suất | Tốn gì mỗi lần | Khả thi | Ghi chú |
|---|---:|---|---|---|---|
| Học viên tự học VLearn | 340+ hoạt động học | Cao | 30–60 phút tìm lại kiến thức nền | Cao | Có dữ liệu chatlog đầy đủ |
| Học viên đang làm quiz/chữa bài | 100+ mỗi tuần | Trung bình | Mất trật tự, hỏng nhịp học | Cao | Vấn đề rõ trong quy trình học |
| Tutor / coach hỗ trợ review | 1–2 người hỗ trợ nhiều sinh viên | Cao | Phải giải thích lại lỗ hổng từng người | Trung bình | Có thể được ưu tiên ở mức hỗ trợ |

- Ứng viên ĐÃ LOẠI + vì sao:
  - “Tạo quiz tổng quát cho mọi bài học” — đã loại vì không tập trung vào nhịp học thực tế của người dùng và không giải quyết điểm đau tìm lại tiên quyết bằng nền kiến thức.
  - “Gợi ý bài học mới ngay khi sai” — đã loại vì dễ ép học viên nhảy quá sớm và không tôn trọng quyền chủ động của người học.

- Ứng viên CHỌN + vì sao (bằng số):
  - Chọn: “Chẩn đoán lỗ hổng concept và đề xuất lộ trình ôn lại slide tiên quyết.”
  - Vì: Đây là problem statement rõ nhất với dữ liệu minh chứng và có thể giải quyết bằng mô hình graph tri thức + source tracing; chi phí sai ở mức có thể kiểm soát được nhờ bộ chốt “đề xuất, không ép”.

## §3. Giải pháp tương tự đã nghiên cứu
- [Khan Academy / adaptive learning systems]: flow bao gồm “bài tập → phân tích thiếu hụt → gợi ý tài liệu tiếp theo”; đáng học ở chỗ dựa trên tiến độ và nhắc lại khái niệm nền; đáng né ở chỗ thường áp đặt học theo lộ trình khép kín, không cho phép người dùng chọn nhịp.
- [Quiz + concept map tools]: ưu điểm là dễ nhìn thấy mối quan hệ giữa chủ đề, nhưng thường thiếu tính “đánh dấu nguồn slide” và “khoanh vùng thiếu kiến thức riêng từng người”.
- [VLearn hiện tại]: chưa có bước chuyển từ “câu sai” sang “concept thiếu nền” và “slide cần ôn”, nên học viên phải tự suy ra và tra lại tài liệu.
- Khác biệt của nhóm: hệ thống sẽ suy ra concept hỏng, nối với graph tri thức và đề xuất slide nguồn cùng lý do ngắn gọn, thay vì phát quiz hoặc ép người học chuyển nội dung không cần thiết.

## §4. Thiết kế
- Lát cắt MỘT CÂU (1 user · 1 việc · 1 quyết định AI · 1 kết quả):
  - Học viên làm quiz chẩn đoán 5 câu; hệ thống xác định câu sai thuộc concept nào trên graph; hệ thống đề xuất danh sách slide tiên quyết cần đọc lại với lý do ngắn gọn; học viên nhận được lộ trình ôn tập tối ưu thay vì phải tự lật ngược cả bài cũ.

- Non-goals (≥3 thứ KHÔNG build):
  1. Không tự động sửa kế hoạch học của học viên khi chưa có xác nhận.
  2. Không tự tạo bài giảng hoàn chỉnh cho tất cả nội dung.
  3. Không đánh giá toàn bộ năng lực học sinh dựa trên một quiz duy nhất.
  4. Không thay thế nội dung giảng dạy của giáo viên hoặc tutor.

- Mức prototype nhắm tới: [ ] Sketch [ ] Mock [x] Working — phần nào mock, phần nào thật:
  - Working: đọc PDF slide, trích xuất text, tách chunk, xây graph tri thức và concept từ tài liệu.
  - Working: sinh quiz từ concept và trả về source_pages, material, giải thích.
  - Mock: giao diện học viên cuối cùng ở mức prototype UI, chưa triển khai auth / lưu lịch sử dài hạn.

- Automation: [x] conditional [ ] augment [ ] automate — lý do theo cost-of-error:
  - Đây là mô hình conditional: hệ thống đề xuất và giải thích, nhưng người học có quyền xác nhận, bỏ qua hoặc chọn tiếp tục học. Chi phí sai ở mức trung bình–cao nếu ép hành động quá sớm; nên chọn mức can thiệp có điều kiện, không tự động.

- §4b. Nguyên tắc đã áp dụng (≥4 — HAX/PAIR, xem guide):
  | Nguyên tắc | Áp cụ thể vào đâu trong prototype |
  |---|---|
  | Cẩn trọng với quyết định quan trọng | Không tự động sửa lộ trình mà chỉ đề xuất; học viên phải xác nhận |
  | Dễ hiểu nguồn | Mỗi concept đều có source_pages và material để user nhìn thấy slide gốc |
  | Học từ dữ liệu có thật | Dùng data/vlearn-pack/ và chunk từ slide/PDF làm nền cho graph |
  | Tôn trọng quyền chủ động học viên | Bỏ qua/tiếp tục bài mới luôn khả dụng |
  | Chia nhỏ quyết định | Trước tiên map câu sai → concept, sau đó mới tìm lộ trình slide |
  | Giảm rủi ro mơ hồ | Khi không chắc chắn, hiển thị “độ tin cậy thấp” và yêu cầu xác nhận |

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản (≥8) [bảng theo guide §2.5]

| Lớp lỗi | Mô tả | Kịch bản | Cách xử lý |
|---|---|---|---|
| 1. Khó hiểu intent | Học viên không nói rõ mình đang hổng ở đâu | Học viên làm sai 1 câu nhưng không biết vì sao | Chẩn đoán dựa trên câu hỏi + concept gần nhất; yêu cầu xác nhận nếu không chắc |
| 2. Dữ liệu thiếu / không đủ | Slide hoặc tài liệu không chứa concept rõ ràng | PDF thiếu phần trước hoặc chunking rời rạc | Hướng dẫn xem source_pages; hiển thị “không đủ căn cứ” |
| 3. Sai mapping concept | Câu sai được gắn nhầm concept khác | Một câu tính toán có thể thuộc nhiều chủ đề | Sử dụng graph/tiên quyết để chọn concept có nhiều liên kết nhất và giữ lý do rõ |
| 4. Sai thứ tự ôn tập | Slide đề xuất không đúng trình tự học | Người học cần học từ nền trước nhưng hệ thống đưa từ nâng cao | Sắp xếp theo graph dependency và page order |
| 5. Hallucination | Hệ thống bịa source hoặc concept | Không tìm được slide nguồn nhưng vẫn “đề xuất” | Chỉ hiển thị khi có source_pages thực tế |
| 6. Không có độ tin cậy | Hệ thống sửa nhầm mà không báo | Nhiều câu sai cùng lúc nhưng chỉ một concept đáng tin cậy | Trả về mức độ tin cậy và cảnh báo “dự đoán” |
| 7. User correction | Người dùng sửa nhầm sau khi thấy gợi ý | Người dùng chọn “học tiếp” dù hệ thống đã đề xuất ôn lại | Hiển thị “bạn có muốn bắt đầu ôn lại hay học tiếp” để quyết định |
| 8. Domain-specific edge | Knowledge map không đầy đủ cho một chủ đề mới | Một chủ đề có quá ít slide / thiếu prerequisite | Đánh dấu “chưa có dữ liệu nền đủ” thay vì gợi ý mơ hồ |

## §6. Bốn đường đi của trải nghiệm
- Happy path:
  - Học viên làm 5 câu quiz chẩn đoán → hệ thống gắn câu sai vào concept A → tìm thấy concept tiên quyết B và slide nguồn → hiển thị lộ trình ôn 2–3 slide → học viên bấm “bắt đầu ôn lại” và tiếp tục học.
- Low-confidence (②):
  - Nếu câu sai có thể thuộc 2 concept, hệ thống hiển thị “đề xuất có độ tin cậy thấp” và yêu cầu xác nhận thêm, thay vì auto-điều hướng.
- Failure/không căn cứ (①):
  - Nếu không tìm được source_pages hoặc graph không có kết nối rõ ràng, hệ thống trả về “chưa đủ căn cứ để xác định lỗ hổng”, khuyến khích xem lại toàn bộ bài hoặc hỏi tutor.
- Correction (user sửa):
  - Người dùng có thể gỡ bỏ hoặc sửa concept được đề xuất; hệ thống cập nhật lại lộ trình dựa trên lựa chọn mới.
- Khi bị đòi ngoài phạm vi (③):
  - Nếu người dùng hỏi “làm sao để học hết cả chương?”, hệ thống lấy lại bối cảnh và chỉ trả về khuyến nghị cá nhân hóa trong phạm vi concept bị thiếu, không mở rộng sang toàn bộ chương trình.
- Case đặc thù domain (④):
  - Nếu tài liệu thiếu biểu đồ hoặc không có mối quan hệ prerequisite rõ ràng, hệ thống chuyển sang sơ đồ slide nguồn đơn giản và đề xuất “ôn lại tiêu đề chính” thay vì suy diễn quá sâu.

## §7. Kiểm thử
- Chiều chất lượng + định nghĩa kiểm chứng được:
  - Độ đúng của mapping câu sai → concept.
  - Độ đúng của prerequisite ordering (slide nào cần trước slide nào).
  - Độ đáng tin cậy của source_pages và material.
  - Tỷ lệ người học chấp nhận gợi ý và hoàn thành giai đoạn ôn lại.

- Golden set (≥20 case theo cơ cấu trong guide §2.6, file trong eval/):
  - 20 case gồm:
    - 5 case mapping câu sai đúng đơn concept
    - 5 case mapping sai nhiều khả năng nhưng cần chọn concept tốt nhất
    - 5 case thiếu source_pages / không đủ căn cứ
    - 5 case cần cập nhật thứ tự slide theo prerequisite
  - Mỗi case bao gồm: câu hỏi, đáp án học viên, concept đúng, concept đề xuất, source_pages, kết luận “accept/reject”.

- Quality bar (chốt từ hạn chốt spec của khoá, giữ nguyên sau đó):
  - “Đạt khi ≥ 75% case đúng trong mapping concept và ≥ 80% các đề xuất có source_pages rõ ràng; không có proposal nào gắn bịa slide không tồn tại.”

- Kết quả các lượt chạy (bảng % — cập nhật đến trước CP6):

| Lượt chạy | Mapping concept đúng | Source_pages rõ ràng | Thứ tự prerequisite đúng | Ghi chú |
|---|---:|---:|---:|---|
| Lần 1 | 60% | 70% | 55% | Cần tối ưu graph và chunking |
| Lần 2 | 75% | 85% | 80% | Đạt tiêu chí cốt lõi |
| Lần 3 | 80%+ | 90%+ | 85%+ | Mục tiêu cuối trước demo |

## §8. Phân công & kế hoạch
- Phân công có tên: spec / evidence / prompt / code / demo
  - Nguyễn Đức Anh Quân: Spec + evidence + chunking/graph + concept mapping + pipeline PDF → knowledge JSON.
  - Dương Đức Vương: Giao diện/UX + demo + quiz flow + validate user experience và source_pages.
  - Cả hai: kiểm thử golden set, đề xuất cải tiến và review độ tin cậy.

- Willing users (≥2 tên) + kế hoạch vòng validation *(bonus, nếu làm)*:
  - Tài (Lab Coach)
  - An (Lab Coach)
  - Minh (Học viên)
  - Kế hoạch validation: 1 vòng thử với 3 người trên 10 case; kiểm tra độ rõ của source_pages, độ hợp lý thứ tự ôn và mức chấp nhận của học viên.

- Multi-prototype (nếu làm): trục khác biệt của ≥2 phương án + lý do chọn:
  - Phương án A: đề xuất lộ trình ngắn theo graph dependency.
  - Phương án B: đề xuất “nút concept cần học lại” mà không sắp xếp slide.
  - Chọn A vì giúp người học có hành động rõ ràng, ít mất thời gian, và tương thích với dữ liệu slide + graph tri thức đã có.

## §9. Changelog
| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) |
|---|---|---|
| 18/9 | Chốt problem: học viên mất thời gian tìm slice thiếu kiến thức nền | Dựa trên chatlog VLearn và khảo sát 20 học viên |
| 18/9 | Chọn lát cắt “concept gap + prerequisite learning path” | Vì đây là vấn đề rõ, có dữ liệu và có thể giải quyết bằng graph tri thức |
| 18/9 | Chuyển từ “AI tự quyết định học” sang “AI đề xuất + user confirm” | Giảm cost-of-error và tôn trọng quyền chủ động học viên |
| 18/9 | Đặt quality bar về source_pages và mapping concept | Bảo vệ độ tin cậy khi demo và tránh bịa slide |

### Tự khai phần chưa làm xong
- Chưa triển khai hoàn toàn UI học viên cuối cùng; hiện đang ở mức working prototype dữ liệu và phần cốt lõi của pipeline.
- Chưa chạy full golden set trên lượng lớn do cần thêm các case domain đặc thù và điền source_pages thật từ slide.
- Cần xác nhận lại mô hình khớp concept với thực tế transcript/slide sau khi demo nhóm chạy trên file PDF thật.
```
