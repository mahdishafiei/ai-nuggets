## Script

Friday evening addition. Two items from today's search window, both on the machine learning side of antibody and immune receptor prediction.

First: AbICL — a new in-context learning framework for antigen-specific antibody affinity ranking, posted this week to arXiv from a team in China. The core contribution is reframing the ranking problem so that a small set of experimentally characterized comparisons for a given antigen can be leveraged at test time without retraining.

Second: a benchmark paper posted yesterday to bioRxiv from a Medical Research Council-funded group at Oxford, asking how well AlphaFold3 actually performs at T-cell receptor antigen specificity prediction — with a high-throughput pipeline that is more than a hundred times faster than the default AlphaFold implementation, and a secondary machine learning model called the PAE Aggregator that improves on the raw structure-prediction scores.

---

**First: AbICL — in-context learning for antigen-specific antibody affinity ranking.**

Paper link: https://arxiv.org/abs/2607.05846

Antibody affinity ranking is the problem of ordering a set of candidate antibodies by how strongly they bind a given target antigen. This is a core operation in lead selection during therapeutic antibody development, and it is nontrivially different from affinity prediction. Regression against absolute affinity values is noisy and assay-dependent. Ranking is more robust — it asks which of two antibodies binds better, not what the exact dissociation constant is — but current ranking methods train a fixed scoring function and apply it independently to each pair of candidates, treating each comparison as isolated.

The isolation assumption is the weakness. Affinity ranking is inherently antigen-specific: whether antibody A beats antibody B depends on the geometry and chemistry of the specific binding pocket you're targeting, and a scoring function trained to generalize across all antigens can't fully encode the idiosyncratic binding landscape of any particular target. For many antigens you work with in practice, you already have some experimental data — a few characterized variants with known relative affinities — before you need to rank the next batch of designs.

AbICL uses that available data directly. It frames antibody affinity ranking as an in-context learning problem. At inference time, it conditions predictions on a support set of labeled affinity comparisons for the same antigen, enabling the model to adapt its scoring to the specific binding landscape without any gradient-based parameter updates. The architecture has three components. First, a pretrained structural encoder converts antibody-antigen complex structures to per-example embeddings. Second, a context ranking head takes both the support set of labeled comparisons and the query pair and processes them jointly, so the ranking decision for the query reflects the patterns visible in the support demonstrations. Third, the model is trained with an episodic meta-training strategy that explicitly simulates the support-query scenario at training time — exposing the model to many episodes of a few labeled examples followed by query predictions — so that it learns to exploit context effectively rather than ignoring it.

On the AbRank benchmark, which provides experimentally characterized pairwise antibody affinity comparisons organized by target antigen, AbICL outperforms both regression and ranking baselines across evaluation splits. The ablations make the contribution of episodic training clear: a model with the same parameter count trained in a standard fashion without episodic structure doesn't show the same context-exploitation behavior, and the performance gap is attributable to learning strategy rather than to model scale.

Two findings from the analysis are worth paying attention to. First, the gains from contextual demonstrations are largest under distribution shift — when the test antigen is dissimilar to the training set, the value of having even a small number of target-specific labeled comparisons increases substantially. This is the situation you're actually in when working on a novel therapeutic target: the training data is by definition not from the same antigen. Second, demonstrations that are biologically related to the test antigen are more informative than random support sets, which implies the model is extracting antigen-specific information from context rather than just using demonstrations as a generic calibration. The relationship between support-set composition and prediction quality degrades gracefully as the demonstrations become less relevant rather than failing abruptly.

The practical framing is this: if you have characterized ten or twenty affinity measurements for a new target as part of early discovery work, AbICL can use those to make better predictions about the next round of candidates than a method that doesn't incorporate that experimental signal. For groups running iterative affinity maturation campaigns where each cycle produces a small number of validated variants, this approach provides a systematic way to get more out of the wet-lab data already in hand.

One limitation the authors flag: the value of in-context learning is bounded by the quality and diversity of the support demonstrations, and in regimes with very few support examples or support sets that are not representative of the test distribution, the gains narrow.

---

**Second: benchmarking AlphaFold3 for T-cell receptor antigen specificity — faster pipeline and a secondary model for improved scores.**

Paper link: https://www.biorxiv.org/content/10.64898/2026.07.08.737208

The second item is a benchmark paper from an Oxford group on what AlphaFold3 actually does well and where it falls short for T-cell receptor antigen specificity prediction.

The context: a T-cell receptor scans peptide fragments presented by major histocompatibility complex molecules on the surface of cells, and recognition of a specific peptide-M-H-C combination triggers an immune response. Predicting which peptides a given receptor recognizes — the T-cell receptor specificity problem — matters for vaccine design, T-cell therapy development, and understanding autoimmunity. Sequence-based computational methods exist but generalize poorly to peptides outside their training distribution. Structure-based methods, in principle, don't rely on sequence-level memorization and could generalize better. The IMMREP twenty-five community benchmark suggested AlphaFold-based approaches outperform sequence-based methods on novel antigens.

This paper is a rigorous follow-up. The practical contribution they make first is a high-throughput pipeline for structure prediction of T-cell receptor to peptide-M-H-C complexes using AlphaFold3 that runs more than one hundred times faster than the default implementation, by batching the inference and precomputing the multiple sequence alignment components. That speedup is what makes systematic benchmarking computationally tractable across large panels of receptor-peptide pairs.

With that infrastructure, they benchmark AlphaFold3's ability to predict T-cell receptor antigen specificity and then ask what the model's scores are actually correlated with mechanistically. The finding is that AlphaFold3's predictive power tracks with the positioning of the T-cell receptor over the peptide-M-H-C complex — the global binding pose — rather than with the specific chemical interactions at the receptor-peptide interface. Put concretely: the model is good at predicting whether the receptor docks in the right orientation over the peptide groove, but not yet at modeling the fine-grained interaction patterns that would distinguish between two similar peptides that the same receptor recognizes with different affinity. This is a meaningful distinction because the former is a structural compatibility question and the latter is a molecular recognition question, and the two come apart in challenging cases.

To improve on the raw AlphaFold3 scores, they train a secondary model they call the PAE Aggregator, which takes the predicted aligned error matrix that AlphaFold3 produces for the structure and learns a refined binding score from it. The PAE Aggregator outperforms the direct AlphaFold3 confidence scores on specificity benchmarks. They also show that AlphaFold3 clusters sequence-similar T-cell receptors according to their binding mode — receptors with similar sequences tend to be predicted to dock in similar poses — and correctly identifies disruptive point mutations in mutational scanning experiments, which is useful for epitope mapping.

The paper's framing is appropriately measured: structure-based approaches show real promise for generalizing to novel antigens, the PAE Aggregator demonstrates that there is additional signal in the AlphaFold3 outputs beyond what the raw confidence scores capture, but the current methods have clear limitations in modeling fine-grained molecular recognition. The hundred-fold inference speedup is a practical contribution the field can use directly.

A note on depth: the full body text of this preprint was not yet rendered through the web proxy when this episode was drafted — this summary is based on the abstract and the preprint landing page. Treat the specific numerical benchmarks as preliminary until the full text is available.

---

Two items this Friday evening. AbICL from a team in China: an in-context learning framework for antigen-specific antibody affinity ranking that uses episodic meta-training and a context ranking head to exploit small support sets of labeled comparisons at test time, with performance gains concentrated under distribution shift and fine-grained affinity discrimination on the AbRank benchmark. And from Oxford: a rigorous benchmark of AlphaFold3 for T-cell receptor antigen specificity, with a hundred-fold inference speedup and a secondary PAE Aggregator model that improves on raw AlphaFold3 scores — finding that AlphaFold3's predictive power tracks with receptor positioning over the complex rather than with fine-grained chemical interactions. Back Monday.
