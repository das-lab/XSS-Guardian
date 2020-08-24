# XSS-Guardian

Cross-Site Scripting Guardian: A Static XSS Detector Based on Data Stream Input-Output Association Mining.

## Research paper

We present the findings of this work in the following research paper:

Li, C.; Wang, Y.; Miao, C.; Huang, C. **Cross-Site Scripting Guardian: A Static XSS Detector Based on Data Stream Input-Output Association Mining**. Appl. Sci. 2020, 10, 4740.

[[PDF]]( https://doi.org/10.3390/app10144740)

## Introduction

The largest number of cybersecurity attacks is on web applications, in which Cross-Site Scripting (XSS) is the most popular way. The code audit is the main method to avoid the damage of XSS at the source code level. However, there are numerous limits implementing manual audits and rule-based audit tools. In the age of big data, it is a new research field to assist the manual auditing through machine learning. In this paper, we propose a new way to audit the XSS vulnerability in PHP source code snippets based on a PHP code parsing tool and the machine learning algorithm. We analyzed the operation sequence of source code and built a model to acquire the information that is most closely related to the XSS attack in the data stream. The method proposed can significantly improve the recall rate of vulnerability samples. Compared with related audit methods, our method has high reusability and excellent performance. Our classification model achieved an F1 score of 0.92, a recall rate of 0.98 (vulnerable sample), and an area under curve (AUC) of 0.97 on the test dataset.

## Reference

If you use *XSS-Guardia* in a scientific publication, we would appreciate citations using this Bibtex entry:

```tex
@article{li2020cross,
  title={Cross-Site Scripting Guardian: A Static XSS Detector Based on Data Stream Input-Output Association Mining},
  author={Li, Chenghao and Wang, Yiding and Miao, Changwei and Huang, Cheng},
  journal={Applied Sciences},
  volume={10},
  number={14},
  pages={4740},
  year={2020},
  publisher={Multidisciplinary Digital Publishing Institute}
}
```

## Notice

- This repo is under construction. See details in [`TODO.md`](./TODO.md).
- To use the tokenizer, click [here](https://github.com/ChanthMiao/VLD) to install the json-patched vld.
- We have tested our tokenizer with the cwe097 dataset in this repo. If it not works with your dataset, you could provide missing handler as we do in `get_sinks.py`.
