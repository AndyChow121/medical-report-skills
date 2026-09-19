# 患者导向证据换算（NNT / NNH）

相对效应（HR/RR/OR）常被夸大感知；患者与临床决策更需要**绝对效应**。`patient_evidence.py`
把相对指标翻译成 NNT（需治疗人数）/ NNH（需伤害人数）与患者友好表述。

## 何时使用

- 把「HR=0.82」变成「每治疗 X 人可多避免 1 例终点」；
- 写 PPT「临床意义」页、患者沟通材料、共享决策（SDM）素材；
- 权衡获益与伤害（同一干预可能既 NNT 又 NNH）。

## 输入

命令行（最常用）或 JSON：

```bash
# 已知两组事件率
python scripts/patient_evidence.py --cer 0.096 --eer 0.091 --event 死亡 --intervention 他汀

# 只有对照组率 + 相对效应，自动推导干预组率
python scripts/patient_evidence.py --cer 0.10 --rr 0.80 --event 死亡
python scripts/patient_evidence.py --cer 0.20 --or 0.5 --event 复发
python scripts/patient_evidence.py --cer 0.30 --hr 0.75 --event 进展   # HR 按 RR 近似
```

推导约定：

| 给入 | 推导 |
|------|------|
| `--rr` | EER = CER × RR |
| `--or` | 先 OR→RR（需 CER）：RR = OR/(1−CER+OR×CER)，再 EER = CER×RR |
| `--hr` | 按 RR 近似（时间-事件终点，仅近似，会标注提醒） |

## 输出指标

- **ARR** 绝对风险降低 = CER − EER（百分点）
- **RRR** 相对风险降低 = ARR / CER
- **NNT** = 1 / ARR（获益时，每治疗多少人避免 1 例事件）
- **NNH** = 1 / ARI（伤害时，每治疗多少人多 1 例伤害）
- **每 1000 人绝对差异** = ARR × 1000
- **患者友好表述**：直接可贴进患者沟通材料的一句话

## 命令

```bash
python scripts/patient_evidence.py --cer 0.096 --eer 0.091 --event 死亡 --intervention 他汀 --out pe.md
python scripts/patient_evidence.py --self-test
```

## 边界

- NNT/NNH 是决策辅助，非个体化预测；具体治疗须结合临床情境、患者偏好与指南。
- OR 在事件率不低时会高估 RR，本工具已按 CER 校正；HR 近似仅作沟通参考。
- 若 ARR≈0（效果极微），NNT 会极大，此时应如实提示「绝对获益极小」。
