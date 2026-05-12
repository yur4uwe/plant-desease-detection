# Experimentation Progress Log

## Experiment Run: 2026-05-11 16:31:27.706279
| Model        |       F1 |   SampleSize |
|:-------------|---------:|-------------:|
| Dummy        | 0.818665 |         5000 |
| RandomForest | 0.900409 |         5000 |
| XGBoost      | 0.892006 |         5000 |
| MobileNetV2  | 0.955765 |         5000 |
| Dummy        | 0.820467 |        10000 |
| RandomForest | 0.905087 |        10000 |
| XGBoost      | 0.906096 |        10000 |
| MobileNetV2  | 0.958977 |        10000 |

## Run: 2026-05-11 19:55:50.053410
| Model       |       F1 |   SampleSize |
|:------------|---------:|-------------:|
| MobileNetV2 | 0.380952 |          100 |

## Run: 2026-05-11 20:01:58.893368
| Model       |   F1 |   SampleSize |
|:------------|-----:|-------------:|
| MobileNetV2 |  0.8 |          100 |

## Run: 2026-05-11 20:36:58.388568
| Model       |       F1 |   SampleSize |
|:------------|---------:|-------------:|
| MobileNetV2 | 0.533333 |          100 |

## Run: 2026-05-11 20:46:24.603011
| Model       |       F1 |   SampleSize |
|:------------|---------:|-------------:|
| MobileNetV2 | 0.857143 |          500 |

## Run: 2026-05-11 21:09:39.776784
| Model       |       F1 |   SampleSize |
|:------------|---------:|-------------:|
| MobileNetV2 | 0.717949 |          500 |

## Run: 2026-05-11 21:16:39.375666
| Model       |       F1 |   SampleSize |
|:------------|---------:|-------------:|
| MobileNetV2 | 0.849057 |          500 |

## Run: 2026-05-12 20:44:11.997094
| Model       |       F1 |   Recall |   Precision |     Latency | Mode         |   SampleSize | Status          |    iNat_F1 |
|:------------|---------:|---------:|------------:|------------:|:-------------|-------------:|:----------------|-----------:|
| Dummy       | 0.93617  | 1        |    0.88     | 5.38826e-07 | standard     |          500 | FAIL (Baseline) | nan        |
| MobileNetV2 | 0.976744 | 0.954545 |    1        | 0.0188867   | standard     |          500 | PASSED          | nan        |
| Dummy       | 0        | 0        |    0        | 4.673e-07   | balanced     |          500 | FAIL (Recall)   | nan        |
| MobileNetV2 | 0.773585 | 0.82     |    0.732143 | 0.0180819   | balanced     |          500 | FAIL (Recall)   |   0.693878 |
| Dummy       | 0.507463 | 1        |    0.34     | 4.43459e-07 | cross_source |          500 | FAIL (Baseline) | nan        |
| MobileNetV2 | 0.328767 | 0.352941 |    0.307692 | 0.0184483   | cross_source |          500 | FAIL (Recall)   |   0.328767 |

## Run: 2026-05-12 22:31:58.055129
| Model        |       F1 |   Recall |   Precision |     Latency | Mode         |   SampleSize | Status                |
|:-------------|---------:|---------:|------------:|------------:|:-------------|-------------:|:----------------------|
| Dummy        | 0.93617  | 1        |    0.88     | 4.33922e-07 | standard     |          500 | FAIL (Below Baseline) |
| XGBoost      | 0.921348 | 0.931818 |    0.911111 | 1.68276e-05 | standard     |          500 | FAIL (Below Baseline) |
| RandomForest | 0.93617  | 1        |    0.88     | 5.60594e-05 | standard     |          500 | FAIL (Below Baseline) |
| MobileNetV2  | 0.946746 | 0.909091 |    0.987654 | 0.0177393   | standard     |          500 | PASSED                |
| Dummy        | 0        | 0        |    0        | 3.95775e-07 | balanced     |          500 | FAIL (Recall)         |
| XGBoost      | 0.654206 | 0.7      |    0.614035 | 1.18089e-05 | balanced     |          500 | FAIL (Recall)         |
| RandomForest | 0.653465 | 0.66     |    0.647059 | 6.04868e-05 | balanced     |          500 | FAIL (Recall)         |
| MobileNetV2  | 0.829787 | 0.78     |    0.886364 | 0.0170608   | balanced     |          500 | FAIL (Recall)         |
| Dummy        | 0.507463 | 1        |    0.34     | 3.8147e-07  | cross_source |          500 | FAIL (Below Baseline) |
| XGBoost      | 0.503937 | 0.941176 |    0.344086 | 9.94682e-06 | cross_source |          500 | FAIL (Below Baseline) |
| RandomForest | 0.507463 | 1        |    0.34     | 5.66792e-05 | cross_source |          500 | FAIL (Below Baseline) |
| MobileNetV2  | 0.48     | 0.882353 |    0.32967  | 0.0173187   | cross_source |          500 | FAIL (Recall)         |

## Run: 2026-05-12 22:33:22.934508
| Model        |       F1 |   Recall |   Precision |     Latency | Mode         |   SampleSize | Status                |
|:-------------|---------:|---------:|------------:|------------:|:-------------|-------------:|:----------------------|
| Dummy        | 0.888889 |    1     |    0.8      | 7.67708e-06 | standard     |           50 | FAIL (Below Baseline) |
| XGBoost      | 0.5      |    0.375 |    0.75     | 0.000140929 | standard     |           50 | FAIL (Recall)         |
| RandomForest | 0.888889 |    1     |    0.8      | 0.000542712 | standard     |           50 | FAIL (Below Baseline) |
| MobileNetV2  | 0.875    |    0.875 |    0.875    | 0.01774     | standard     |           50 | FAIL (Recall)         |
| Dummy        | 0        |    0     |    0        | 3.91006e-06 | balanced     |           50 | FAIL (Recall)         |
| XGBoost      | 0.5      |    0.4   |    0.666667 | 8.22306e-05 | balanced     |           50 | FAIL (Recall)         |
| RandomForest | 0.285714 |    0.2   |    0.5      | 0.000523257 | balanced     |           50 | FAIL (Recall)         |
| MobileNetV2  | 0.545455 |    0.6   |    0.5      | 0.0164625   | balanced     |           50 | FAIL (Recall)         |
| Dummy        | 0.181818 |    1     |    0.1      | 3.67165e-06 | cross_source |           50 | FAIL (Below Baseline) |
| XGBoost      | 0.181818 |    1     |    0.1      | 8.04663e-05 | cross_source |           50 | FAIL (Below Baseline) |
| RandomForest | 0.181818 |    1     |    0.1      | 0.000532889 | cross_source |           50 | FAIL (Below Baseline) |
| MobileNetV2  | 0.181818 |    1     |    0.1      | 0.0204287   | cross_source |           50 | FAIL (Below Baseline) |

## Run: 2026-05-12 22:38:13.310791
| Model        |       F1 |   Recall |   Precision |     Latency | Mode         |   SampleSize | Status                |
|:-------------|---------:|---------:|------------:|------------:|:-------------|-------------:|:----------------------|
| Dummy        | 0.888889 |    1     |    0.8      | 4.14848e-06 | standard     |           50 | FAIL (Below Baseline) |
| XGBoost      | 0.5      |    0.375 |    0.75     | 0.000105786 | standard     |           50 | FAIL (Recall)         |
| RandomForest | 0.888889 |    1     |    0.8      | 0.000513816 | standard     |           50 | FAIL (Below Baseline) |
| MobileNetV2  | 0.75     |    0.75  |    0.75     | 0.0178908   | standard     |           50 | FAIL (Recall)         |
| Dummy        | 0        |    0     |    0        | 3.95775e-06 | balanced     |           50 | FAIL (Recall)         |
| XGBoost      | 0.5      |    0.4   |    0.666667 | 8.33035e-05 | balanced     |           50 | FAIL (Recall)         |
| RandomForest | 0.285714 |    0.2   |    0.5      | 0.000499344 | balanced     |           50 | FAIL (Recall)         |
| MobileNetV2  | 0.615385 |    0.8   |    0.5      | 0.0154381   | balanced     |           50 | FAIL (Recall)         |
| Dummy        | 0.181818 |    1     |    0.1      | 3.86238e-06 | cross_source |           50 | FAIL (Below Baseline) |
| XGBoost      | 0.181818 |    1     |    0.1      | 9.02414e-05 | cross_source |           50 | FAIL (Below Baseline) |
| RandomForest | 0.181818 |    1     |    0.1      | 0.000496793 | cross_source |           50 | FAIL (Below Baseline) |
| MobileNetV2  | 0.181818 |    1     |    0.1      | 0.0169625   | cross_source |           50 | FAIL (Below Baseline) |

## Run: 2026-05-12 22:41:41.956074
| Model        |       F1 |   Recall |   Precision |     Latency | Mode         |   SampleSize | Status                |
|:-------------|---------:|---------:|------------:|------------:|:-------------|-------------:|:----------------------|
| Dummy        | 0.888889 |    1     |    0.8      | 4.05312e-06 | standard     |           50 | FAIL (Below Baseline) |
| XGBoost      | 0.5      |    0.375 |    0.75     | 9.00745e-05 | standard     |           50 | FAIL (Recall)         |
| RandomForest | 0.888889 |    1     |    0.8      | 0.000510192 | standard     |           50 | FAIL (Below Baseline) |
| MobileNetV2  | 0.714286 |    0.625 |    0.833333 | 0.0178587   | standard     |           50 | FAIL (Recall)         |
| Dummy        | 0        |    0     |    0        | 3.74317e-06 | balanced     |           50 | FAIL (Recall)         |
| XGBoost      | 0.5      |    0.4   |    0.666667 | 8.51393e-05 | balanced     |           50 | FAIL (Recall)         |
| RandomForest | 0.25     |    0.2   |    0.333333 | 0.00050149  | balanced     |           50 | FAIL (Recall)         |
| MobileNetV2  | 0.5      |    0.6   |    0.428571 | 0.0157395   | balanced     |           50 | FAIL (Recall)         |
| Dummy        | 0.181818 |    1     |    0.1      | 3.71933e-06 | cross_source |           50 | FAIL (Below Baseline) |
| XGBoost      | 0.181818 |    1     |    0.1      | 7.89881e-05 | cross_source |           50 | FAIL (Below Baseline) |
| RandomForest | 0.181818 |    1     |    0.1      | 0.000513268 | cross_source |           50 | FAIL (Below Baseline) |
| MobileNetV2  | 0.181818 |    1     |    0.1      | 0.0165859   | cross_source |           50 | FAIL (Below Baseline) |

## Run: 2026-05-12 22:51:51.393664
| Model        |       F1 |   Recall |   Precision |     Latency | Mode         |   SampleSize | Status                |
|:-------------|---------:|---------:|------------:|------------:|:-------------|-------------:|:----------------------|
| Dummy        | 0.93617  | 1        |    0.88     | 4.48227e-07 | standard     |          500 | FAIL (Below Baseline) |
| XGBoost      | 0.921348 | 0.931818 |    0.911111 | 1.06406e-05 | standard     |          500 | FAIL (Below Baseline) |
| RandomForest | 0.93617  | 1        |    0.88     | 6.00863e-05 | standard     |          500 | FAIL (Below Baseline) |
| MobileNetV2  | 0.947368 | 0.920455 |    0.975904 | 0.0185677   | standard     |          500 | PASSED                |
| Dummy        | 0        | 0        |    0        | 5.29289e-07 | balanced     |          500 | FAIL (Recall)         |
| XGBoost      | 0.654206 | 0.7      |    0.614035 | 1.32823e-05 | balanced     |          500 | FAIL (Recall)         |
| RandomForest | 0.672897 | 0.72     |    0.631579 | 6.68693e-05 | balanced     |          500 | FAIL (Recall)         |
| MobileNetV2  | 0.787234 | 0.74     |    0.840909 | 0.0179406   | balanced     |          500 | FAIL (Recall)         |
| Dummy        | 0.507463 | 1        |    0.34     | 4.02927e-07 | cross_source |          500 | FAIL (Below Baseline) |
| XGBoost      | 0.503937 | 0.941176 |    0.344086 | 1.01876e-05 | cross_source |          500 | FAIL (Below Baseline) |
| RandomForest | 0.507463 | 1        |    0.34     | 6.04653e-05 | cross_source |          500 | FAIL (Below Baseline) |
| MobileNetV2  | 0.373832 | 0.588235 |    0.273973 | 0.0178451   | cross_source |          500 | FAIL (Recall)         |

## Run: 2026-05-13 00:48:03.791674
| Model        |       F1 |   Recall |   Precision |     Latency | Mode         |   SampleSize | Status                |
|:-------------|---------:|---------:|------------:|------------:|:-------------|-------------:|:----------------------|
| Dummy        | 0.935037 | 1        |    0.878    | 5.43594e-08 | standard     |         5000 | FAIL (Below Baseline) |
| XGBoost      | 0.965129 | 0.977221 |    0.953333 | 1.63078e-06 | standard     |         5000 | PASSED                |
| RandomForest | 0.966814 | 0.995444 |    0.939785 | 1.05052e-05 | standard     |         5000 | PASSED                |
| MobileNetV2  | 0.969417 | 0.95672  |    0.982456 | 0.0334795   | standard     |         5000 | PASSED                |
| Dummy        | 0        | 0        |    0        | 4.93526e-08 | balanced     |         5000 | FAIL (Recall)         |
| XGBoost      | 0.832161 | 0.828    |    0.836364 | 2.90942e-06 | balanced     |         5000 | FAIL (Recall)         |
| RandomForest | 0.832507 | 0.84     |    0.825147 | 1.67499e-05 | balanced     |         5000 | FAIL (Recall)         |
| MobileNetV2  | 0.928429 | 0.934    |    0.922925 | 0.027857    | balanced     |         5000 | PASSED                |
| Dummy        | 0.530492 | 1        |    0.361    | 1.13249e-07 | cross_source |         5000 | FAIL (Below Baseline) |
| XGBoost      | 0.467898 | 0.736842 |    0.342784 | 2.59757e-06 | cross_source |         5000 | FAIL (Recall)         |
| RandomForest | 0.529412 | 0.99723  |    0.36036  | 1.22938e-05 | cross_source |         5000 | FAIL (Below Baseline) |
| MobileNetV2  | 0.370649 | 0.545706 |    0.280627 | 0.0238402   | cross_source |         5000 | FAIL (Recall)         |

## Run: 2026-05-13 01:17:03.536963
| Model        |       F1 |   Recall |   Precision |     Latency |     TrainTime | Mode         |   SampleSize | Status                |
|:-------------|---------:|---------:|------------:|------------:|--------------:|:-------------|-------------:|:----------------------|
| Dummy        | 0.93617  | 1        |    0.88     | 8.7738e-07  |   0.000284672 | standard     |          500 | FAIL (Below Baseline) |
| XGBoost      | 0.933333 | 0.954545 |    0.913043 | 1.56275e-05 |   0.933625    | standard     |          500 | FAIL (Below Baseline) |
| RandomForest | 0.93617  | 1        |    0.88     | 0.000103556 |   0.196717    | standard     |          500 | FAIL (Below Baseline) |
| MobileNetV2  | 0.976744 | 0.954545 |    1        | 0.0290982   | 146.198       | standard     |          500 | PASSED                |
| Dummy        | 0        | 0        |    0        | 7.47045e-07 |   0.000508547 | balanced     |          500 | FAIL (Recall)         |
| XGBoost      | 0.658228 | 0.702703 |    0.619048 | 1.65431e-05 |   1.70399     | balanced     |          500 | FAIL (Recall)         |
| RandomForest | 0.756098 | 0.837838 |    0.688889 | 0.000108109 |   0.173077    | balanced     |          500 | FAIL (Recall)         |
| MobileNetV2  | 0.906667 | 0.918919 |    0.894737 | 0.0262685   | 130.824       | balanced     |          500 | PASSED                |
| Dummy        | 0.5      | 1        |    0.333333 | 6.58035e-07 |   0.000279903 | cross_source |          500 | FAIL (Below Baseline) |
| XGBoost      | 0.484848 | 0.96     |    0.324324 | 2.10317e-05 |   0.713418    | cross_source |          500 | FAIL (Below Baseline) |
| RandomForest | 0.5      | 1        |    0.333333 | 9.84637e-05 |   0.157609    | cross_source |          500 | FAIL (Below Baseline) |
| MobileNetV2  | 0.404762 | 0.68     |    0.288136 | 0.0290242   | 159.593       | cross_source |          500 | FAIL (Recall)         |
