# Reference verification (Reviewer 2: "unverified citations")

Method. Every reference of the submitted manuscript was checked with web
search (direct access to arXiv, Crossref, Semantic Scholar and publisher
pages is blocked by this environment's egress policy, so evidence comes from
index pages and abstracts returned by search). Status codes:

* **V** — existence and bibliographic details confirmed by an independent index page.
* **V\*** — standard, widely cited reference; bibliographic details match the commonly cited record but were not individually re-searched here.
* **C** — exists, but the manuscript's bibliographic details or the claim attributed to it were wrong; corrected in the revision.
* **N** — could not be found; removed from the revision (authors should restore it only with a DOI/URL).

Quantitative claims attributed to a reference are kept in the revision only if a source states them.

| # | Submitted citation | Status | Finding / action |
|---|---|---|---|
| 1 | Tseng et al., CHI 2022 | C | Exists (doi 10.1145/3491102.3517728). It concerns misuse of virtual-physical perceptual manipulations (redirected walking, haptics) to cause physical harm, not "optical flow / binocular disparity inducing nausea without tripping intrusion detection". Description corrected. |
| 2 | Kundu et al., "Securing VR experiences…", IEEE TDSC 2025 | C | Exists (arXiv:2503.13419; NSF-PAR lists IEEE TDSC 22(6):6040–6057). Method: adversarial examples fool DL cybersickness detectors; SHAP-based "XAI signatures" + RF/XGBoost/FFNN detect them; datasets "Simulation 2021" and a "Gameplay" dataset (racing + flight games, 35 participants, 22 columns — very likely the same UFFCSData release used here). Abstract-level sources report ~90 % / ~94 %; **the manuscript's 93.5 % accuracy and ~35 ms SHAP latency could not be found and were removed** (Tables 1–2, Secs. I, II-C). |
| 3 | V. Nair et al., "Explainable and real-time detection in immersive VR systems", 2023 | N | Not found. Removed. |
| 4 | Dennison, Wisti, D'Zmura, Displays 44:42–52, 2016 | C | Exists (doi 10.1016/j.displa.2016.07.002). Studied EGG, blinking, breathing; the "SVM on GSR and HR, ~85 %" description is unsupported. Described qualitatively. |
| 5 | R. Islam et al., ISMAR 2020 | C | Exists: "Automatic detection and prediction of cybersickness severity using deep neural networks from user's physiological signals". Uses SVM + deep neural classifiers, not random forests on EDA/IMU; "~85 %" unsupported. Corrected. |
| 6 | Y. Liu et al., CNN-ECA-LSTM, 2024 | C | M. Liu, B. Yang, M. Xu, P. Zan, L. Chen, X. Xia, Displays 81:102602, 2024. "92 %" not verified; removed. |
| 7 | D. Jeong, S. Yoo, Y. Jang, "MAC: multimodal attention-based cybersickness prediction", 2023 | N | Not found with these authors. Removed. |
| 8 | D. Jeong, S. Han, "Transformer-based multimodal fusion for VR cybersickness prediction", 2024 | C | Probably D. Jeong and K. Han, "PRECYSE: Predicting cybersickness using transformer for multimodal time-series sensor data", 2024; venue to be confirmed by the authors. |
| 9 | X. Ma et al., hierarchical attention, 2024 | N | Not found. Removed. |
| 10 | Caserman et al., Virtual Reality 25(4):1153–1170, 2021 | V\* | Kept. |
| 11 | Y. Yang et al., "Limitations of static supervised classifiers for cybersickness detection", 2022 | C | Title not found; replaced by A. H. X. Yang, N. Kasabov, Y. O. Cakmak, "Machine learning methods for the study of cybersickness: a systematic review", Brain Informatics 9:24, 2022. |
| 12 | Mnih et al., Nature 2015 | V\* | Kept. |
| 13 | van Hasselt, Guez, Silver, AAAI 2016 | V\* | Kept. |
| 14 | Kennedy et al., SSQ, 1993 | V\* | Kept. |
| 15 | P. Kourtesis et al., review of measurement and mitigation, 2024 | N | No such 2024 review found (Kourtesis et al. 2023 CSQ-VR exists). Removed. |
| 16 | Yalcin & Halbig, BiLSTM + GAN, 2024 | C | M. Yalcin, A. Halbig, M. Fischbach, M. E. Latoschik, Frontiers in Virtual Reality 5:1364207, 2024 (91.1 % F1). Authors completed. |
| 17 | C. Qu et al., eye-tracking CNN, 2022 | N | Not found. Removed (Table 1 row). |
| 18 | B. Odeleye et al., 2023 | C | Correct title "Virtually secure: A taxonomic assessment of cybersecurity challenges in virtual reality environments", Computers & Security 124:102951, 2023. |
| 19 | A. Ubeysinghe, perceptual manipulation survey, 2024 | N | Not found. Removed; Cheng et al., USENIX Security 2023 (verified) cited instead where needed. |
| 20 | Valluripally, Gulhane, Hoque, Calyam, IEEE TSC 15(5), 2022 | C | Correct: 8 authors (Valluripally, Frailey, Kruse, Palipatana, Oruche, Gulhane, Hoque, Calyam), IEEE TSC 16(4):2559–2574, 2023, doi 10.1109/TSC.2022.3216539. Addresses network DoS/unauthorised access, not cybersickness induction. |
| 21 | Valluripally et al., "Attack-resilient and explainable detection for social VRLEs", 2023 | N | Not found. Removed. |
| 22 | M. Naeem et al., federated DDQN for network intrusion, 2025 | N | Not found. Removed (Table 3 rows "Federated DDQN" and "RL anomaly prioritisation"). |
| 23 | Giaretta, Virtual Reality 29(1), 2024 | C | Virtual Reality 29:10, 2025, doi 10.1007/s10055-024-01079-9. |
| 24 | Lundberg & Lee, NeurIPS 2017 | V\* | Kept. |
| 25 | Ribeiro et al., KDD 2016 | V\* | Kept. |
| 26 | TruVR, ISMAR 2022, pp. 777–786 | C | Exists (Kundu, Islam, Calyam, Hoque). Reports 99.75 % (physiological) and 94.10 % (gameplay) accuracy — **not 91.3 %**. Corrected. |
| 27 | LiteVR, IEEE VR 2023 | C | Exists (Kundu, Islam, Quarles, Hoque). Reports ~94 % accuracy — **not 89.7 %**. Corrected. |
| 28 | D. Karapiperis et al., SHAP + LIME IDS, 2025 | N | Not found. Removed (Table 2 row, 98.5 %). |
| 29 | Sutton & Barto, 2018 | V\* | Kept for the MDP formalism; it is **not** a source for "safe-RL shows asymmetric penalties yield risk-conservative policies" — García & Fernández, JMLR 2015 is cited for that instead. |
| 30 | He & Garcia, TKDE 2009 | V\* | Kept for imbalanced learning; it was mis-cited for "robust quartile scaling of HMD telemetry" (removed). |
| 31–42 | Wang (dueling), Ioffe & Szegedy, Srivastava, Glorot & Bengio, Girshick, Lillicrap, Kingma & Ba, Loshchilov & Hutter, Lin 1992, Elkan, Williams & Zipser, Chicco & Jurman | V\* | Kept where still cited (Glorot & Bengio and Williams & Zipser are no longer needed after the removal of Xavier-initialisation details and teacher forcing). |

## Added references (all V)

Porcino et al. (UFFCSData GitHub; Entertainment Computing 2022; XR in Games 2021 methodology) — dataset provenance; Odeleye et al., VR4Sec 2021 (frame-rate manipulation attacks inducing VR sickness); Cheng et al., USENIX Security 2023; Islam, Desai, Quarles, ISMAR 2021 pp. 31–40 (87.77 %); VR-LENS (arXiv:2302.01985); Lin, Chen, Qi, Applied Intelligence 2020 (DQN with class-asymmetric rewards — prior art for the reward design); García & Fernández, JMLR 2015; Lattimore & Szepesvári 2020 (bandits); Kapoor & Narayanan, Patterns 2023; Kaufman et al., TKDD 2012; Roberts et al., Ecography 2017; Varma & Simon 2006; McNemar 1947; Dietterich 1998; Saito & Rehmsmeier 2015; Chawla et al. 2002; Shrikumar et al. 2017; Goodfellow et al. 2015; Madry et al. 2018; Pedregosa et al. 2011; Paszke et al. 2019. (Classic entries are V\*; dataset, attack and leakage entries were checked by search.)

## Summary

* 9 references could not be found (3, 7, 9, 15, 17, 19, 21, 22, 28) and were removed.
* 15 had wrong bibliographic details or misattributed content (1, 2, 4, 5, 6, 8, 11, 16, 18, 20, 23, 26, 27, 29, 30, including claim-level corrections) and were corrected.
* The two numbers singled out by Reviewer 2 (93.5 % and ~35 ms for [2]) are **not supported** by any accessible source and do not appear in the revision.
