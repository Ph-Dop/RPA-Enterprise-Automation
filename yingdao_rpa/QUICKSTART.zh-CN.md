# 影刀流程搭建速通（中文）

目标：在影刀里搭一个 `order_crawl` 流程，爬取模拟后台网页，写入 CSV，再调用 Python 流水线。

## 准备：打开模拟后台

影刀要爬的"订单后台"已经给你做好了，双击打开：
`C:\Users\ASDIY\RPA-Enterprise-Automation\data\mock_web\index.html`
（这是个本地网页，长得像真实订单后台，表格里有 15 条订单）

## 搭建步骤（在影刀客户端里）

1. **新建应用**：影刀首页 → 新建应用 → 命名 `order_crawl`
2. **打开网页**：拖入「打开网页」指令 → 网址填：
   ```
   file:///C:/Users/ASDIY/RPA-Enterprise-Automation/data/mock_web/index.html
   ```
3. **等待表格加载**：拖入「等待元素出现」→ 指向网页里的订单表格
4. **抓取表格**：拖入「获取网页数据表格」指令 → 框选整个表格 → 输出到一个变量 `dtOrders`
5. **循环遍历**：拖入「数据循环」→ 遍历 `dtOrders`，每轮取出
   `order_id / customer / ordered_at / product / amount / status` 六列
6. **追加写 CSV**：在循环内拖入「写入CSV/Excel」→ 路径填：
   ```
   C:\Users\ASDIY\RPA-Enterprise-Automation\data\raw\orders_raw.csv
   ```
   写入方式选「追加行」，列顺序与上面六列一致
7. **运行 Python 流水线**：循环结束后，拖入「运行命令行/Python脚本」指令，执行：
   ```
   C:\Users\ASDIY\RPA-Enterprise-Automation\.venv\Scripts\python.exe C:\Users\ASDIY\RPA-Enterprise-Automation\run_demo.py
   ```
8. **异常保护**：用「Try-Catch」把步骤 3~7 包起来，Catch 里写「记录日志 + 弹窗提示人工介入」
9. **运行一次**：点右上角运行，观察 CSV 是否追加了 15 行、报表是否生成
10. **导出工程**：影刀内「导出」→ 把 `.rdx` 文件放进本目录（`yingdao_rpa/`），然后 git 提交

## 面试怎么讲

> "Yingdao RPA 负责网页操作（登录、抓表格），通过 CSV 和 Python 解耦——
> Python 侧做清洗、报表、告警。即使没有 Yingdao，整个流程也能通过 mock/API 通道跑通，
> 这就是 dual-channel 设计。"
