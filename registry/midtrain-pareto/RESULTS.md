# Released midtraining checkpoint on the capability-behavior plane

## Question

Where does the released Model-Spec Midtraining plus alignment-fine-tuning
checkpoint sit relative to the released alignment-fine-tuning-only checkpoint?
All comparison arms were co-measured in one evaluation session.

## Result

| arm | GPQA | parse rate | murder | exfiltration | mean AM |
|---|---:|---:|---:|---:|---:|
| base | 0.697 | 0.975 | 0.413 | 0.413 | 0.413 |
| AFT only | 0.460 | 0.672 | 0.047 | 0.200 | 0.123 |
| MSM + AFT | 0.566 | 0.803 | 0.087 | 0.000 | 0.043 |
| AFT + mixed replay | 0.687 | 0.960 | 0.017 | 0.020 | 0.018 |

The midtrained checkpoint had higher GPQA and lower aggregate AM than the
AFT-only checkpoint. The aggregate AM improvement came entirely from
exfiltration falling from 0.200 to 0.000; murder rose from 0.047 to 0.087.
Therefore the aggregate should not be described as an unqualified safety gain.

## Caveats

The GPQA confidence intervals for MSM+AFT and AFT-only overlap. Five of six
pre-registered anchor legs passed; the mixed-replay murder anchor was lower than
its standing value. Base and the full GPQA scale reproduced, supporting the
comparability of the new point while leaving the low-rate murder deviation
flagged.
