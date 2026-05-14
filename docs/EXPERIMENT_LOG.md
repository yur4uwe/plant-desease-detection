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

## Run: 2026-05-13 16:37:49.578690
| Model        |       F1 |   Recall |   Precision |     Latency |    TrainTime | Mode     |   SampleSize | Status                |
|:-------------|---------:|---------:|------------:|------------:|-------------:|:---------|-------------:|:----------------------|
| Dummy        | 0.888889 | 1        |    0.8      | 7.62939e-06 |  0.000728846 | standard |          100 | FAIL (Below Baseline) |
| XGBoost      | 0.75     | 0.75     |    0.75     | 7.75655e-05 |  0.373187    | standard |          100 | FAIL (Recall)         |
| RandomForest | 0.888889 | 1        |    0.8      | 0.000512918 |  0.181667    | standard |          100 | FAIL (Below Baseline) |
| MobileNetV2  | 0.631579 | 0.5      |    0.857143 | 0.0238619   | 24.5751      | standard |          100 | FAIL (Recall)         |
| Dummy        | 0        | 0        |    0        | 3.16302e-06 |  0.000277758 | balanced |          100 | FAIL (Recall)         |
| XGBoost      | 0.4      | 0.428571 |    0.375    | 7.65959e-05 |  0.403038    | balanced |          100 | FAIL (Recall)         |
| RandomForest | 0.5      | 0.428571 |    0.6      | 0.000491683 |  0.111807    | balanced |          100 | FAIL (Recall)         |
| MobileNetV2  | 0.75     | 0.857143 |    0.666667 | 0.0229949   | 24.4288      | balanced |          100 | FAIL (Recall)         |

## Run: 2026-05-13 16:40:14.390728
| Model        |       F1 |   Recall |   Precision |     Latency |    TrainTime | Mode     |   SampleSize | Status                |
|:-------------|---------:|---------:|------------:|------------:|-------------:|:---------|-------------:|:----------------------|
| Dummy        | 0.888889 | 1        |    0.8      | 3.7988e-06  |  0.000288963 | standard |          100 | FAIL (Below Baseline) |
| XGBoost      | 0.75     | 0.75     |    0.75     | 7.90278e-05 |  0.249078    | standard |          100 | FAIL (Recall)         |
| RandomForest | 0.888889 | 1        |    0.8      | 0.000479794 |  0.10182     | standard |          100 | FAIL (Below Baseline) |
| MobileNetV2  | 0.833333 | 0.833333 |    0.833333 | 0.0236256   | 24.4335      | standard |          100 | FAIL (Recall)         |
| Dummy        | 0        | 0        |    0        | 3.25839e-06 |  0.000287056 | balanced |          100 | FAIL (Recall)         |
| XGBoost      | 0.470588 | 0.571429 |    0.4      | 7.92503e-05 |  0.358049    | balanced |          100 | FAIL (Recall)         |
| RandomForest | 0.615385 | 0.571429 |    0.666667 | 0.000483084 |  0.128164    | balanced |          100 | FAIL (Recall)         |
| MobileNetV2  | 0.666667 | 0.571429 |    0.8      | 0.0246044   | 24.7958      | balanced |          100 | FAIL (Recall)         |

## Run: 2026-05-13 16:53:52.681544
| Model        |       F1 |   Recall |   Precision |     Latency |    TrainTime | Mode     |   SampleSize | Status                |
|:-------------|---------:|---------:|------------:|------------:|-------------:|:---------|-------------:|:----------------------|
| Dummy        | 0.888889 | 1        |    0.8      | 3.91006e-06 |  0.00032258  | standard |          100 | FAIL (Below Baseline) |
| XGBoost      | 0.8      | 0.833333 |    0.769231 | 7.35124e-05 |  0.30147     | standard |          100 | FAIL (Recall)         |
| RandomForest | 0.888889 | 1        |    0.8      | 0.000475486 |  0.13049     | standard |          100 | FAIL (Below Baseline) |
| MobileNetV2  | 0.923077 | 1        |    0.857143 | 0.026418    | 26.9006      | standard |          100 | PASSED                |
| Dummy        | 0        | 0        |    0        | 3.5127e-06  |  0.000301123 | balanced |          100 | FAIL (Recall)         |
| XGBoost      | 0.4      | 0.428571 |    0.375    | 0.000156546 |  0.395676    | balanced |          100 | FAIL (Recall)         |
| RandomForest | 0.5      | 0.428571 |    0.6      | 0.00050993  |  0.109509    | balanced |          100 | FAIL (Recall)         |
| MobileNetV2  | 0.444444 | 0.285714 |    1        | 0.0273043   | 25.8173      | balanced |          100 | FAIL (Recall)         |

## Run: 2026-05-13 16:58:42.665945
| Model        |       F1 |   Recall |   Precision |     Latency |    TrainTime | Mode         |   SampleSize | Status                |
|:-------------|---------:|---------:|------------:|------------:|-------------:|:-------------|-------------:|:----------------------|
| Dummy        | 0.888889 | 1        |    0.8      | 2.74976e-06 |  0.000253201 | standard     |          100 | FAIL (Below Baseline) |
| XGBoost      | 0.75     | 0.75     |    0.75     | 4.433e-05   |  0.159598    | standard     |          100 | FAIL (Recall)         |
| RandomForest | 0.888889 | 1        |    0.8      | 0.000333246 |  0.0703132   | standard     |          100 | FAIL (Below Baseline) |
| MobileNetV2  | 0.8      | 0.833333 |    0.769231 | 0.0232281   | 19.1003      | standard     |          100 | FAIL (Recall)         |
| Dummy        | 0        | 0        |    0        | 2.44776e-06 |  0.000212193 | balanced     |          100 | FAIL (Recall)         |
| XGBoost      | 0.615385 | 0.571429 |    0.666667 | 6.03358e-05 |  0.205899    | balanced     |          100 | FAIL (Recall)         |
| RandomForest | 0.6      | 0.428571 |    1        | 0.000332848 |  0.0712867   | balanced     |          100 | FAIL (Recall)         |
| MobileNetV2  | 0.769231 | 0.714286 |    0.833333 | 0.0188904   | 19.0747      | balanced     |          100 | FAIL (Recall)         |
| Dummy        | 0.421053 | 1        |    0.266667 | 2.36829e-06 |  0.000206709 | cross_source |          100 | FAIL (Below Baseline) |
| XGBoost      | 0.421053 | 1        |    0.266667 | 4.60307e-05 |  0.136216    | cross_source |          100 | FAIL (Below Baseline) |
| RandomForest | 0.421053 | 1        |    0.266667 | 0.00033741  |  0.0695159   | cross_source |          100 | FAIL (Below Baseline) |
| MobileNetV2  | 0.25     | 0.5      |    0.166667 | 0.0184557   | 22.0657      | cross_source |          100 | FAIL (Recall)         |

## Run: 2026-05-13 17:30:39.006275
| Model        |       F1 |   Recall |   Precision |     Latency |     TrainTime | Mode         |   SampleSize | Status                |
|:-------------|---------:|---------:|------------:|------------:|--------------:|:-------------|-------------:|:----------------------|
| Dummy        | 0.93617  | 1        |    0.88     | 1.43687e-06 |   0.000538111 | standard     |          500 | FAIL (Below Baseline) |
| XGBoost      | 0.933333 | 0.954545 |    0.913043 | 1.42352e-05 |   0.598764    | standard     |          500 | FAIL (Below Baseline) |
| RandomForest | 0.93617  | 1        |    0.88     | 7.35219e-05 |   0.113246    | standard     |          500 | FAIL (Below Baseline) |
| MobileNetV2  | 0.984615 | 0.969697 |    1        | 0.0291344   | 120.085       | standard     |          500 | PASSED                |
| Dummy        | 0.658228 | 1        |    0.490566 | 7.42247e-07 |   0.000226974 | balanced     |          500 | FAIL (Below Baseline) |
| XGBoost      | 0.576923 | 0.576923 |    0.576923 | 2.61406e-05 |   0.938816    | balanced     |          500 | FAIL (Recall)         |
| RandomForest | 0.701754 | 0.769231 |    0.645161 | 0.000124068 |   0.130747    | balanced     |          500 | FAIL (Recall)         |
| MobileNetV2  | 0.8      | 0.923077 |    0.705882 | 0.0263975   |  86.8275      | balanced     |          500 | PASSED                |
| Dummy        | 0.5      | 1        |    0.333333 | 5.75384e-07 |   0.000258446 | cross_source |          500 | FAIL (Below Baseline) |
| XGBoost      | 0.494845 | 0.96     |    0.333333 | 1.32116e-05 |   0.501205    | cross_source |          500 | FAIL (Below Baseline) |
| RandomForest | 0.5      | 1        |    0.333333 | 7.70982e-05 |   0.131961    | cross_source |          500 | FAIL (Below Baseline) |
| MobileNetV2  | 0.494845 | 0.96     |    0.333333 | 0.0269214   | 142.729       | cross_source |          500 | FAIL (Below Baseline) |

## Run: 2026-05-13 17:54:21.113646
| Model        |       F1 |   Recall |   Precision |     Latency |     TrainTime | Mode         |   SampleSize | Status                |
|:-------------|---------:|---------:|------------:|------------:|--------------:|:-------------|-------------:|:----------------------|
| Dummy        | 0.93617  | 1        |    0.88     | 6.23067e-07 |   0.000271082 | standard     |          500 | FAIL (Below Baseline) |
| XGBoost      | 0.948905 | 0.984848 |    0.915493 | 2.15054e-05 |   0.537711    | standard     |          500 | PASSED                |
| RandomForest | 0.93617  | 1        |    0.88     | 8.0169e-05  |   0.128293    | standard     |          500 | FAIL (Below Baseline) |
| MobileNetV2  | 0.96875  | 0.939394 |    1        | 0.0247358   | 113.116       | standard     |          500 | PASSED                |
| Dummy        | 0.658228 | 1        |    0.490566 | 7.64739e-07 |   0.000236988 | balanced     |          500 | FAIL (Below Baseline) |
| XGBoost      | 0.576923 | 0.576923 |    0.576923 | 2.01486e-05 |   0.831643    | balanced     |          500 | FAIL (Recall)         |
| RandomForest | 0.571429 | 0.538462 |    0.608696 | 0.000106713 |   0.106695    | balanced     |          500 | FAIL (Recall)         |
| MobileNetV2  | 0.777778 | 0.807692 |    0.75     | 0.0259375   |  80.9631      | balanced     |          500 | FAIL (Recall)         |
| Dummy        | 0.5      | 1        |    0.333333 | 1.00454e-06 |   0.000496864 | cross_source |          500 | FAIL (Below Baseline) |
| XGBoost      | 0.484848 | 0.96     |    0.324324 | 1.35008e-05 |   0.577667    | cross_source |          500 | FAIL (Below Baseline) |
| RandomForest | 0.5      | 1        |    0.333333 | 9.02843e-05 |   0.127802    | cross_source |          500 | FAIL (Below Baseline) |
| MobileNetV2  | 0.5      | 1        |    0.333333 | 0.0265405   | 141.675       | cross_source |          500 | FAIL (Below Baseline) |

## Run: 2026-05-13 18:10:03.430766
| Model        |       F1 |   Recall |   Precision |     Latency |     TrainTime | Mode         |   SampleSize | Status                |
|:-------------|---------:|---------:|------------:|------------:|--------------:|:-------------|-------------:|:----------------------|
| Dummy        | 0.93617  | 1        |    0.88     | 6.19888e-07 |   0.000244617 | standard     |          500 | FAIL (Below Baseline) |
| XGBoost      | 0.941176 | 0.969697 |    0.914286 | 1.38251e-05 |   0.533881    | standard     |          500 | PASSED                |
| RandomForest | 0.93617  | 1        |    0.88     | 8.30364e-05 |   0.121103    | standard     |          500 | FAIL (Below Baseline) |
| MobileNetV2  | 0.96875  | 0.939394 |    1        | 0.0298057   | 118.109       | standard     |          500 | PASSED                |
| Dummy        | 0.658228 | 1        |    0.490566 | 1.01665e-06 |   0.0003016   | balanced     |          500 | FAIL (Below Baseline) |
| XGBoost      | 0.64     | 0.615385 |    0.666667 | 3.11024e-05 |   1.1028      | balanced     |          500 | FAIL (Recall)         |
| RandomForest | 0.653061 | 0.615385 |    0.695652 | 0.000118269 |   0.119879    | balanced     |          500 | FAIL (Recall)         |
| MobileNetV2  | 0.857143 | 0.807692 |    0.913043 | 0.026744    |  84.3901      | balanced     |          500 | FAIL (Recall)         |
| Dummy        | 0.5      | 1        |    0.333333 | 5.40415e-07 |   0.000235319 | cross_source |          500 | FAIL (Below Baseline) |
| XGBoost      | 0.5      | 1        |    0.333333 | 1.34087e-05 |   0.459528    | cross_source |          500 | FAIL (Below Baseline) |
| RandomForest | 0.5      | 1        |    0.333333 | 8.21972e-05 |   0.125294    | cross_source |          500 | FAIL (Below Baseline) |
| MobileNetV2  | 0.426966 | 0.76     |    0.296875 | 0.0272023   | 141.203       | cross_source |          500 | FAIL (Recall)         |



| Model        |       F1 |   Recall |   Precision |     Latency |      TrainTime | Mode         |   SampleSize | Status                |
|:-------------|---------:|---------:|------------:|------------:|---------------:|:-------------|-------------:|:----------------------|
| Dummy        | 0.861912 | 1        |    0.757333 | 6.29425e-08 |    0.00028801  | standard     |         5000 | FAIL (Below Baseline) |
| XGBoost      | 0.912434 | 0.917254 |    0.907666 | 2.26688e-06 |    2.28315     | standard     |         5000 | PASSED                |
| RandomForest | 0.908939 | 0.957746 |    0.864865 | 1.37113e-05 |    0.846537    | standard     |         5000 | PASSED                |
| MobileNetV2  | 0.955036 | 0.934859 |    0.976103 | 0.0224281   |  992.49        | standard     |         5000 | PASSED                |
| Dummy        | 0.672481 | 1        |    0.506569 | 1.62194e-07 |    0.00154185  | balanced     |         5000 | FAIL (Below Baseline) |
| XGBoost      | 0.797784 | 0.829971 |    0.768    | 2.39741e-06 |    3.0915      | balanced     |         5000 | FAIL (Recall)         |
| RandomForest | 0.810229 | 0.867435 |    0.760101 | 1.59354e-05 |    0.864571    | balanced     |         5000 | FAIL (Recall)         |
| MobileNetV2  | 0.882801 | 0.835735 |    0.935484 | 0.0233225   |  958.503       | balanced     |         5000 | FAIL (Recall)         |
| Dummy        | 0        | 0        |    0        | 5.8492e-08  |    0.000273705 | cross_source |         5000 | FAIL (Recall)         |
| XGBoost      | 0.526741 | 0.9631   |    0.3625   | 2.46652e-06 |    2.25241     | cross_source |         5000 | PASSED                |
| RandomForest | 0.526527 | 0.97048  |    0.361264 | 1.38613e-05 |    0.86516     | cross_source |         5000 | PASSED                |
| MobileNetV2  | 0.516949 | 0.900369 |    0.362556 | 0.0226513   | 1057.31        | cross_source |         5000 | PASSED                |


| Model       |       F1 |   Recall |   Precision |     Latency |     TrainTime | Mode         |   SampleSize | Status                |
|:------------|---------:|---------:|------------:|------------:|--------------:|:-------------|-------------:|:----------------------|
| Dummy       | 0.867925 | 1        |    0.766667 | 2.81334e-07 |   0.000278711 | standard     |         1000 | FAIL (Below Baseline) |
| MobileNetV2 | 0.905172 | 0.913043 |    0.897436 | 0.020923    | 198.188       | standard     |         1000 | PASSED                |
| Dummy       | 0        | 0        |    0        | 2.55903e-07 |   0.000225782 | balanced     |         1000 | FAIL (Recall)         |
| MobileNetV2 | 0.747967 | 0.613333 |    0.958333 | 0.0219919   | 197.418       | balanced     |         1000 | FAIL (Recall)         |
| Dummy       | 0        | 0        |    0        | 2.55903e-07 |   0.000262499 | cross_source |         1000 | FAIL (Recall)         |
| MobileNetV2 | 0.649573 | 0.655172 |    0.644068 | 0.0226815   | 205.233       | cross_source |         1000 | FAIL (Recall)         |


| Model       |       F1 |   Recall |   Precision |     Latency |     TrainTime | Mode         |   SampleSize | Status                |
|:------------|---------:|---------:|------------:|------------:|--------------:|:-------------|-------------:|:----------------------|
| Dummy       | 0.867925 | 1        |    0.766667 | 2.97228e-07 |   0.000242472 | standard     |         1000 | FAIL (Below Baseline) |
| XGBoost     | 0.87931  | 0.886957 |    0.871795 | 7.59125e-06 |   0.91098     | standard     |         1000 | FAIL (Recall)         |
| MobileNetV2 | 0.925764 | 0.921739 |    0.929825 | 0.0215235   | 201.387       | standard     |         1000 | PASSED                |
| Dummy       | 0        | 0        |    0        | 2.54313e-07 |   0.000221491 | balanced     |         1000 | FAIL (Recall)         |
| XGBoost     | 0.728477 | 0.733333 |    0.723684 | 9.55264e-06 |   1.76761     | balanced     |         1000 | FAIL (Recall)         |
| MobileNetV2 | 0.837838 | 0.826667 |    0.849315 | 0.0223104   | 207.253       | balanced     |         1000 | FAIL (Recall)         |
| Dummy       | 0        | 0        |    0        | 2.54313e-07 |   0.000220776 | cross_source |         1000 | FAIL (Recall)         |
| XGBoost     | 0.578035 | 0.862069 |    0.434783 | 8.07126e-06 |   0.988716    | cross_source |         1000 | FAIL (Recall)         |
| MobileNetV2 | 0.654206 | 0.603448 |    0.714286 | 0.0230999   | 210.452       | cross_source |         1000 | FAIL (Recall)         |
