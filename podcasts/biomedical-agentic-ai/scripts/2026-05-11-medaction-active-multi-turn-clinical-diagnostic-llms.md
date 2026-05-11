# 2026-05-11 — MedAction: train LLMs to act under partial evidence, not just reason over complete information

Paper link: https://arxiv.org/abs/2605.07305

## Script

Welcome back. Monday, May eleventh, twenty-twenty-six. Today's nugget is a clinical-reasoning paper that puts a name on something the feed has been circling for a couple of weeks — the gap between how medical large language models are trained and how clinicians actually work.

The paper is "MedAction: Towards Active Multi-turn Clinical Diagnostic Large Language Models." Posted to arXiv on Friday, May eighth. The senior author is Liyue Shen at Michigan, and the author list mixes her group with clinical collaborators.

Here is the setup. Almost every medical LLM evaluation today is single turn. The patient case is dumped into the prompt all at once — history, symptoms, labs, imaging, the works — and the model produces a diagnosis. The MedAction authors point out that this is not what doctors do. Real diagnosis is active. You start with an observation, you order one or two tests, you read the results, you update your differential, you order more tests, you converge. Multi-turn. Partial evidence at every step. The decision of what to do next is part of the task.

Their systematic analysis identifies three failure modes when frontier models try to do this. First, ungrounded test ordering — the model asks for tests it would not actually use, or skips tests that would change the differential. Second, unreliable diagnostic update — when a test result comes back, the model does not update its hypothesis in a way that tracks the evidence. Third, degraded multi-turn coherence — the model loses thread over a long case, forgets earlier observations, or contradicts its own earlier reasoning.

The diagnosis they offer is the headline. Existing medical training data teaches models to reason from complete information but not to act under evolving partial evidence. That is a clean way to put it, and it explains a lot. The medical-textbook corpus, the case-report corpus, even the doctor-patient-dialogue corpora — they are all written in retrospect. By the time someone writes the case up, the relevant tests have already been ordered, the relevant findings already filtered, and the narrative arc points at the right diagnosis. There is no observed cost of ordering a useless test, no observed branch where the clinician went down the wrong differential for two turns and backed out.

MedAction is the proposed fix. It is a tree-structured distillation pipeline that synthesizes diverse multi-turn diagnostic trajectories by letting a teacher model interact with a clinical environment. The environment carries the case. The model proposes a test. The environment returns the result. The model updates and proposes the next test. Trajectories branch and the tree gets pruned. The interesting trick is how the trajectories get filtered, because not every synthetic dialogue is useful training data.

They propose two metrics, both grounded in a medical knowledge graph. The first is Disease Trajectory Consistency — does the model's running hypothesis converge toward the correct diagnosis over the dialogue, or does it drift away. The second is Reasoning-Action Consistency — when the model updates its belief, is the update actually driven by the evidence it just gathered, or is it making things up. Using these two metrics to filter, they keep the trajectories that show real, evidence-driven convergence and throw out the ones that are confused or confabulating. That is what gets distilled into the student model. Both metrics use the knowledge graph as ground truth for what counts as an evidence-to-hypothesis link — which is the kind of methodological move where having a real biomedical knowledge graph in your toolkit pays off, rather than just text similarity.

The output dataset is MedAction-32K. Thirty-two thousand six hundred and eighty-one synthesized trajectories drawn from twenty-eight hundred ninety-six published clinical cases. Fine-tuning an eight-billion-parameter open-source model on this set gets state of the art among open-source medical models on the standard multi-turn benchmark, and on a harder hold-out the authors curate themselves.

Two reasons to pay attention.

First, the gap framing is correct and durable. Other papers will run on this framing for the next year. "Trained to reason on complete information, not to act under partial evidence" is the kind of one-line problem statement that survives whatever specific eight-billion-parameter model gets fine-tuned this quarter. Open-source medical LLMs that ignore this gap will keep saturating single-turn benchmarks and failing multi-turn ones.

Second, the use of a knowledge graph as the ground-truth substrate for both trajectory-consistency metrics is a clean example of a pattern we will see more of. Rather than the knowledge graph being the answer source — the way it gets used in retrieval-augmented setups — it is being used as the *referee* for whether a chain of reasoning is well-grounded. That is a job the knowledge graph is uniquely suited for and that a free-text scorer cannot do reliably.

One caveat worth flagging. The two metrics depend on the knowledge graph being right. If the graph is missing a disease-symptom edge, the metric will downweight a perfectly correct trajectory. The biomedical knowledge graphs we have today are not complete, and the failure mode on a long tail of rare diseases is exactly the place where active diagnosis matters most. Watch for the v2 of this kind of work to use a more comprehensive graph, and to publish per-disease accuracy alongside the aggregate.

That is it for today. Back tomorrow.
