# 🕸️ Web-Based Crawling & Website Categorization System

> Automated pipeline that crawls and classifies **10,000+ URLs per execution** into predefined categories with **92%+ classification accuracy** — published as a peer-reviewed research paper.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Maven](https://img.shields.io/badge/Maven-C71A36?style=flat-square&logo=apachemaven&logoColor=white)
![Accuracy](https://img.shields.io/badge/Classification_Accuracy-92%25+-success?style=flat-square)
![URLs](https://img.shields.io/badge/URLs_per_execution-10%2C000+-blue?style=flat-square)
![Research](https://img.shields.io/badge/Research_Paper-Published_2024-orange?style=flat-square)

---

## 📄 Research Paper

> **"Web-Based Crawling to Categorize Websites into 'N' Categories"**
> Deepti Pujari · Published 2024
>
> 🔗 **[Read the paper →](#)** ← *https://ijrar.org/papers/IJRAR24B3448.pdf*

This repository is the working implementation accompanying the paper. The system design, categorization methodology, and accuracy benchmarks described in the paper are directly reflected in this codebase.

---

## 📊 Results at a Glance

| Metric | Result |
|---|---|
| URLs processed per execution | **10,000+** |
| Classification accuracy | **92%+** |
| Manual effort reduction | **~60%** |
| Processing time (pre-automation) | **~8 hours** |
| Processing time (post-automation) | **< 2 hours** |
| Supported category count | **N (configurable)** |

---

## 🏗️ System Architecture

```
  Input: URL list (file / stdin)
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │                    Crawling Pipeline                      │
  │                                                          │
  │  ┌─────────────┐   ┌──────────────┐   ┌──────────────┐  │
  │  │  URL Queue  │──►│   Crawler    │──►│  Raw Content │  │
  │  │  Manager    │   │  (requests + │   │   Extractor  │  │
  │  │             │   │  BeautifulS) │   │  (text/meta) │  │
  │  └─────────────┘   └──────────────┘   └──────┬───────┘  │
  └──────────────────────────────────────────────┼───────────┘
                                                 │
                                                 ▼
  ┌──────────────────────────────────────────────────────────┐
  │                 Categorization Engine                     │
  │                                                          │
  │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐ │
  │  │   Feature    │──►│  Classifier  │──►│   Category   │ │
  │  │  Extraction  │   │  (rule-based │   │  Assignment  │ │
  │  │  (TF-IDF /   │   │  + ML model) │   │  + Scoring   │ │
  │  │   keywords)  │   │              │   │              │ │
  │  └──────────────┘   └──────────────┘   └──────┬───────┘ │
  └──────────────────────────────────────────────┼──────────┘
                                                 │
                                                 ▼
  ┌──────────────────────────────────────────────────────────┐
  │                      Output Layer                         │
  │                                                          │
  │   CSV report  ·  JSON export  ·  Accuracy metrics        │
  └──────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

- **High-throughput crawling** — processes 10,000+ URLs per run with configurable concurrency and politeness delays
- **N-category classification** — categories are fully configurable via `categories.json`; no code changes needed to add or rename categories
- **92%+ accuracy** — validated against a manually labelled ground-truth dataset of 1,000+ URLs (see paper for methodology)
- **Content + metadata extraction** — uses page title, meta description, heading tags, and body text for multi-signal classification
- **Fault-tolerant pipeline** — skips unreachable URLs, logs failures separately, and resumes from checkpoint on interruption
- **Structured output** — results exported as CSV and JSON with URL, assigned category, confidence score, and crawl timestamp
- **Maven build integration** — reproducible builds and dependency management for the Java utility components

---

## 🗂️ Project Structure

```
web-crawling-categorization-system/
├── src/
│   ├── crawler/
│   │   ├── url_queue.py          # URL queue manager with deduplication
│   │   ├── crawler.py            # Core crawling logic (requests + retries)
│   │   └── content_extractor.py  # HTML parsing, text + metadata extraction
│   ├── categorizer/
│   │   ├── feature_extractor.py  # TF-IDF vectorisation, keyword extraction
│   │   ├── classifier.py         # Category assignment + confidence scoring
│   │   └── categories.json       # Category definitions (fully configurable)
│   ├── output/
│   │   ├── reporter.py           # CSV + JSON export
│   │   └── metrics.py            # Accuracy, precision, recall computation
│   └── main.py                   # Entry point — orchestrates full pipeline
├── data/
│   ├── sample_urls.txt           # Sample input: 100 URLs to try the system
│   └── ground_truth.csv          # Labelled dataset used for accuracy validation
├── tests/
│   ├── test_crawler.py
│   ├── test_classifier.py
│   └── test_feature_extractor.py
├── results/
│   └── sample_output.csv         # Example output for 100 URLs
├── pom.xml                       # Maven build for Java utility components
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

**Prerequisites:** Python 3.10+

```bash
# 1. Clone the repo
git clone https://github.com/deepti-pujari/web-crawling-categorization-system.git
cd web-crawling-categorization-system

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run on the sample URL list
python src/main.py --input data/sample_urls.txt --output results/output.csv

# 4. Run on your own URL list
python src/main.py --input your_urls.txt --output results/my_output.csv --categories src/categorizer/categories.json
```

---

## ⚙️ Configuration

### CLI Arguments

```
python src/main.py [OPTIONS]

  --input       Path to input file (one URL per line)         [required]
  --output      Path for CSV output file                       [required]
  --categories  Path to categories JSON config  [default: categories.json]
  --workers     Concurrent crawl workers        [default: 10]
  --delay       Politeness delay between requests (sec)  [default: 0.5]
  --timeout     Per-URL request timeout (sec)   [default: 10]
  --checkpoint  Resume from checkpoint file     [optional]
```

### Category Configuration (categories.json)

```json
{
  "categories": [
    {
      "name": "Technology",
      "keywords": ["software", "programming", "developer", "API", "cloud", "AI"],
      "domains": ["github.com", "stackoverflow.com"]
    },
    {
      "name": "Finance",
      "keywords": ["banking", "investment", "insurance", "loan", "premium", "policy"],
      "domains": ["rbi.org.in", "sebi.gov.in"]
    },
    {
      "name": "Healthcare",
      "keywords": ["hospital", "medicine", "doctor", "diagnosis", "treatment", "health"],
      "domains": []
    }
  ]
}
```

Add or remove categories here — no code changes required.

---

## 🔑 Core Components

### Crawler (crawler.py)

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor

class WebCrawler:
    def __init__(self, workers: int = 10, delay: float = 0.5, timeout: int = 10):
        self.workers = workers
        self.delay = delay
        self.timeout = timeout
        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.5,
                      status_forcelist=[429, 500, 502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retry))
        session.mount("http://",  HTTPAdapter(max_retries=retry))
        return session

    def crawl_batch(self, urls: list[str]) -> list[dict]:
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            results = list(executor.map(self._crawl_one, urls))
        return [r for r in results if r is not None]

    def _crawl_one(self, url: str) -> dict | None:
        try:
            response = self.session.get(url, timeout=self.timeout,
                                        headers={"User-Agent": "ResearchCrawler/1.0"})
            response.raise_for_status()
            return {"url": url, "status": response.status_code,
                    "html": response.text, "final_url": response.url}
        except Exception as e:
            return {"url": url, "status": "ERROR", "error": str(e), "html": None}
```

### Classifier (classifier.py)

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class WebsiteClassifier:
    def __init__(self, categories: list[dict]):
        self.categories = categories
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
        self._build_category_profiles()

    def _build_category_profiles(self):
        """Build a TF-IDF profile for each category from its keyword list."""
        category_docs = [" ".join(cat["keywords"]) for cat in self.categories]
        self.category_vectors = self.vectorizer.fit_transform(category_docs)

    def classify(self, text: str) -> tuple[str, float]:
        """Return (category_name, confidence_score) for the given page text."""
        page_vector = self.vectorizer.transform([text])
        similarities = cosine_similarity(page_vector, self.category_vectors).flatten()
        best_idx = int(np.argmax(similarities))
        confidence = float(similarities[best_idx])
        return self.categories[best_idx]["name"], round(confidence, 4)
```

---

## 📈 Accuracy & Evaluation

Accuracy was validated against a manually labelled ground-truth dataset of **1,000+ URLs** spanning all supported categories. See the paper for full methodology.

```
Overall Accuracy:    92.4%
Macro Precision:     91.8%
Macro Recall:        90.6%
Macro F1 Score:      91.2%

Per-category breakdown (sample):
  Technology   →  Precision: 95.1%  Recall: 94.3%
  Finance      →  Precision: 93.7%  Recall: 91.2%
  Healthcare   →  Precision: 90.4%  Recall: 89.8%
  ...
```

To reproduce accuracy metrics against the included ground truth dataset:

```bash
python src/main.py --input data/ground_truth.csv --output results/eval.csv
python src/output/metrics.py --predicted results/eval.csv --ground-truth data/ground_truth.csv
```

---

## 📤 Sample Output

```csv
url,category,confidence,status,crawled_at
https://github.com,Technology,0.9721,SUCCESS,2024-03-15T10:22:01Z
https://rbi.org.in,Finance,0.9534,SUCCESS,2024-03-15T10:22:03Z
https://aiims.edu,Healthcare,0.9108,SUCCESS,2024-03-15T10:22:05Z
https://broken-site.xyz,,0.0000,ERROR,2024-03-15T10:22:07Z
```

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing
```

---

## 📦 Dependencies

```
requests==2.31.0
beautifulsoup4==4.12.2
scikit-learn==1.4.0
numpy==1.26.4
pandas==2.2.0
lxml==5.1.0
pytest==8.0.0
pytest-cov==4.1.0
```

Install all: `pip install -r requirements.txt`

---

## 📄 Citation

If you use this system or reference the methodology in your work, please cite:

```bibtex
@article{pujari2024webcrawling,
  title   = {Web-Based Crawling to Categorize Websites into 'N' Categories},
  author  = {Pujari, Deepti},
  year    = {2024},
  url     = {<your publication link>}
}
```

---

## 👩‍💻 Author

**Deepti Pujari** — Java Software Development Engineer · CS Research  
[LinkedIn](https://linkedin.com/in/deepti-pujari) · [GitHub](https://github.com/deepti-pujari) · [deeptipujari02@gmail.com](mailto:deeptipujari02@gmail.com)
