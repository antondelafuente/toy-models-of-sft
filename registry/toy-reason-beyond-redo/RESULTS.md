# Capability checks beyond GPQA

## Question

Does the capability difference between off-model and student-written rewrites
extend beyond GPQA? The valid rerun evaluated animal-welfare and
self-preservation organisms across three seeds on GPQA, a 400-question MMLU
subset, and a 400-question MATH subset. Trait liveness was checked separately.

## Result

- GPQA: the animal-welfare off-model arms scored 0.540-0.596, while the
  student-written arms scored 0.641-0.667. The separation reproduced across
  three seeds.
- MMLU: all trained arms clustered around 0.795-0.828 against a 0.830 base.
  There was no clear off-model versus student-written separation.
- MATH: trained arms scored about 0.793-0.890 against a 0.913 base. The result
  looked more like a general adapter cost than an off-model-specific cost.

## Validity and caveats

Every capability arm had a passing trait-liveness proof on a relevant serving
process. Five MATH arms completed 390-391 of 400 questions at a firm cutover;
unfinished items were counted wrong in the fixed-denominator primary metric.
Only two representative MATH arms received a same-process semantic liveness
check; the remaining arms had same-process mechanical adapter checks and
cross-process semantic checks.

The earlier `toy-reason-beyond-rerun` GPQA/MMLU result is invalid because of a
silent adapter-serving failure. Only this corrected record should support the
paper's beyond-GPQA statement.
