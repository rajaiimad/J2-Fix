# Interim reference-verification notes (web search, 2026-10-12)

Tools: WebSearch only (direct HTTP to arxiv.org, crossref, semantic scholar,
publisher sites is blocked by this environment's egress policy; WebFetch fails).
"Verified" = bibliographic existence confirmed by >=1 independent index page.
Numerical claims are only "verified" if a source states the number.

| # | Manuscript citation | Status | Finding |
|---|---|---|---|
| 1 | Tseng et al., CHI 2022 | VERIFIED | W.-J. Tseng, E. Bonnail, M. McGill, M. Khamis, E. Lecolinet, S. Huron, J. Gugenheimer, CHI '22, doi 10.1145/3491102.3517728. Paper is about virtual-physical perceptual manipulations (redirected walking/haptics) causing physical harm; it is NOT about optical-flow/binocular-disparity cybersickness induction "without tripping intrusion detection" as the manuscript states. |
| 2 | Kundu et al., "Securing VR experiences...", IEEE TDSC 2025 | EXISTS; NUMBERS UNVERIFIED | arXiv:2503.13419 (Kundu, Denton, Mongalo, Calyam, Hoque); NSF-PAR lists IEEE TDSC 22(6):6040-6057. Method: adversarial examples (CleverHans) against DL cybersickness detectors; SHAP "XAI signatures" + RF/XGBoost/FFNN to detect them; datasets "Simulation 2021" and "Gameplay". The 93.5 % accuracy and ~35 ms SHAP latency could not be found in any accessible source -> remove. |
| 4 | Dennison, Wisti, D'Zmura, Displays 44:42-52, 2016 | EXISTS; CLAIM UNVERIFIED | doi 10.1016/j.displa.2016.07.002. Measured EGG, blinking, breathing; the "SVM on GSR and HR, ~85 %" description could not be confirmed (secondary sources: heart rate NOT associated). |
| 5 | R. Islam et al., ISMAR 2020 | EXISTS; DESCRIPTION WRONG | "Automatic detection and prediction of cybersickness severity using deep neural networks from user's physiological signals" (Islam, Lee, Jaloli, ... Quarles), ISMAR 2020. Uses SVM + deep neural classifiers (CNN-LSTM), not random forests on EDA/IMU; the "~85 %" figure is not supported. |
| 6 | Y. Liu et al., CNN-ECA-LSTM, 2024 | EXISTS (authors/venue corrected) | M. Liu, B. Yang, M. Xu, P. Zan, L. Chen, X. Xia, "Exploring quantitative assessment of cybersickness in virtual reality using EEG signals and a CNN-ECA-LSTM network," Displays 81:102602, 2024. The "92 %" accuracy is unverified. |
| 7 | D. Jeong, S. Yoo, Y. Jang, "MAC...", 2023 | NOT FOUND | Two searches failed to locate the paper or the author list. Flag for author verification / removal. |
| 10 | Caserman et al., Virtual Reality 25(4):1153-1170, 2021 | (well known) | Caserman, Garcia-Agundez, Gamez Zerban, Goebel - to be kept. |
| 11 | Y. Yang et al., "Limitations of static supervised classifiers for cybersickness detection," 2022 | TITLE NOT FOUND | Closest real paper: A. Yang, N. Kasabov, Y. O. Cakmak, "Machine learning methods for the study of cybersickness: a systematic review," Brain Informatics 9:24, 2022, doi 10.1186/s40708-022-00172-6. Replace. |
| 15 | Kourtesis et al., review 2024 | NOT FOUND as cited | No 2024 Kourtesis review on measurement & mitigation found. Kourtesis, Linnell, Amir 2023 (CSQ-VR) exists. Replace or remove. |
| 16 | Yalcin & Halbig, BiLSTM + GAN, 2024 | EXISTS (authors incomplete) | M. Yalcin, A. Halbig, M. Fischbach, M. E. Latoschik, Frontiers in Virtual Reality 5:1364207, 2024; BiLSTM + conditional-GAN augmentation, 91.1 % F1. |
| 17 | C. Qu et al., eye-tracking CNN, 2022 | NOT FOUND | Flag / remove. |
| 18 | Odeleye et al., 2023 | EXISTS (title corrected) | B. Odeleye, G. Loukas, R. Heartfield, G. Sakellari, E. Panaousis, F. Spyridonis, "Virtually secure: A taxonomic assessment of cybersecurity challenges in virtual reality environments," Computers & Security 124:102951, 2023. |
| 23 | Giaretta, Virtual Reality 29(1), 2024 | EXISTS (volume/year corrected) | A. Giaretta, "Security and privacy in virtual reality: a literature survey," Virtual Reality 29:10, 2025, doi 10.1007/s10055-024-01079-9. |
| 26 | TruVR, ISMAR 2022 pp. 777-786 | EXISTS; NUMBER WRONG | Kundu, Islam, Calyam, Hoque. Reports 99.75 % (physiological) and 94.10 % (gameplay) accuracy, not 91.3 %. |
| 27 | LiteVR, IEEE VR 2023 | EXISTS; NUMBER WRONG | Kundu, Islam, Quarles, Hoque. Reports ~94 % accuracy (lite LSTM), not 89.7 %. |
| D | Dataset | ADDED | T. Porcino et al., UFFCSData, https://github.com/tmp1986/UFFCSData ; Porcino, Rodrigues, Bernardini, Trevisan, Clua, "Identifying cybersickness causes in virtual reality games using symbolic machine learning algorithms," Entertainment Computing (ScienceDirect PII S1875952121000707), 2022; methodology paper in SBC XR in Games 2021 (doi 10.5753/xr_in_games.2021.15681). |
| 3 | V. Nair et al., "Explainable and real-time detection in immersive VR systems," 2023 | NOT FOUND | No such paper located. Remove; the latency-vs-explainability argument should cite VR-LENS / LiteVR (Kundu et al.) instead. |
| 8 | D. Jeong & S. Han, "Transformer-based multimodal fusion for VR cybersickness prediction," 2024 | TITLE NOT FOUND; probable intended work | D. Jeong and K. Han, "PRECYSE: Predicting cybersickness using transformer for multimodal time-series sensor data," 2024 (venue to be confirmed by authors). |
| 9 | X. Ma et al., hierarchical attention, 2024 | NOT FOUND | Remove. |
| 19 | A. Ubeysinghe, perceptual manipulation survey, 2024 | NOT FOUND | Remove; cite Cheng et al., "Exploring user reactions and mental models towards perceptual manipulation attacks in mixed reality," USENIX Security 2023 (verified) if needed. |
| 20 | Valluripally, Gulhane, Hoque, Calyam, IEEE TSC 15(5) 2022 | EXISTS (authors/volume corrected) | S. Valluripally, B. Frailey, B. Kruse, B. Palipatana, R. Oruche, A. Gulhane, K. A. Hoque, P. Calyam, IEEE Trans. Services Computing 16(4):2559-2574, 2023, doi 10.1109/TSC.2022.3216539. Detects network DoS / unauthorised access - not cybersickness induction. |
| 22 | M. Naeem et al., federated DDQN, 2025 | NOT FOUND | Remove (Table 3 rows "Federated DDQN" and "RL anomaly prioritisation" lose their only source). |
| 28 | D. Karapiperis et al., SHAP+LIME IDS, 2025 | NOT FOUND | Remove (Table 2 row and the 98.5 % figure). |
| new | Odeleye, Loukas, Heartfield, Spyridonis, "Detecting framerate-oriented cyber attacks on user experience in virtual reality," VR4Sec workshop (with SOUPS 2021), pp. 1-5 | VERIFIED | Directly relevant to the Type I (frame-pacing) threat; Isolation-Forest early warning of frame-rate manipulation. |
| new | Cheng et al., USENIX Security 2023, perceptual manipulation attacks in MR | VERIFIED | Optional support for the perceptual-attack framing. |
