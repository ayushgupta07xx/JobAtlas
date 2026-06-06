# JobAtlas — Process Maps

BPMN-style swim-lane diagrams for the three core flows: the job-seeker journey, the recruiter journey, and the scrape-to-warehouse data flow. Mermaid has no native BPMN pool/lane element, so each lane is represented as a labelled `subgraph`. Solid arrows are process flow; dotted arrows are analytics events.

---

## 1. Job-seeker journey

How a seeker (Anjali / Rohit / Sneha) moves from arrival to a matched application, across the frontend, API and analytics.

```mermaid
flowchart TB
  subgraph SEEKER["Lane - Job Seeker"]
    S1([Start - open JobAtlas])
    S2[Enter search query + filters]
    S3[Upload resume]
    S4{Review results}
    S5[Save job to shortlist]
    S6[Click Apply]
    S7([End - redirected to source])
  end
  subgraph FE["Lane - JobAtlas Frontend"]
    F1[Submit search]
    F2[Render ranked results]
    F3[Request match]
    F4[Show match score + skill overlap]
  end
  subgraph API["Lane - JobAtlas API"]
    A1[Semantic + filter search]
    A2[Embed resume BGE-small 384-dim]
    A3[pgvector HNSW retrieval + score]
  end
  subgraph PH["Lane - Analytics"]
    P1[(search_executed)]
    P2[(match_requested)]
    P3[(apply_clicked)]
  end

  S1 --> S2 --> F1 --> A1 --> F2 --> S4
  S1 --> S3 --> F3 --> A2 --> A3 --> F4 --> S4
  S4 -->|relevant| S5
  S4 -->|apply| S6 --> S7
  F1 -.-> P1
  F3 -.-> P2
  S6 -.-> P3
```

---

## 2. Recruiter journey

How a recruiter benchmarks a company's hiring by searching one name and receiving all aggregated, deduplicated openings.

```mermaid
flowchart TB
  subgraph REC["Lane - Recruiter"]
    R1([Start - open JobAtlas])
    R2[Search company name]
    R3{Review aggregated openings}
    R4[Benchmark hiring activity]
    R5[Open posting at source]
    R6([End])
  end
  subgraph FE["Lane - JobAtlas Frontend"]
    F1[Submit company query]
    F2[Render deduped results + source + posted date]
    F3[Sort by recency]
  end
  subgraph API["Lane - JobAtlas API"]
    A1[Company search across index]
    A2[Collapse duplicates - canonical record]
    A3[Return sorted postings]
  end

  R1 --> R2 --> F1 --> A1 --> A2 --> A3 --> F2 --> F3 --> R3
  R3 -->|compare| R4 --> R6
  R3 -->|inspect| R5 --> R6
```

---

## 3. Scrape-to-warehouse data flow

How postings move from source to warehouse: ingestion, raw landing, normalisation, dedup, embeddings, transformation, and a quality gate.

```mermaid
flowchart TB
  subgraph SRC["Lane - Sources"]
    C1[Adzuna API]
    C2[Jobicy API]
    C3[ATS feeds - Greenhouse/Lever/Ashby/TheMuse]
  end
  subgraph ING["Lane - Ingestion (Airflow + Scrapy)"]
    I1[daily_scrape DAG]
    I2[API clients / spiders]
  end
  subgraph RAW["Lane - Raw Zone (MongoDB)"]
    M1[(raw payloads)]
  end
  subgraph OPS["Lane - Operational (Postgres + pgvector)"]
    N1[Normalizer to staging.jobs]
    N2[MinHash dedup - Jaccard ≥ 0.85]
    N3[Embeddings BGE-small to pgvector]
  end
  subgraph XF["Lane - Transformation + Quality"]
    D1[dbt staging to marts]
    D2[SCD Type 2 dim_job]
    D3{Great Expectations gate}
    Q1[Quarantine + alert]
  end
  subgraph WH["Lane - Warehouse (demo)"]
    W1[(BigQuery / Snowflake marts)]
  end

  C1 --> I1
  C2 --> I1
  C3 --> I1
  I1 --> I2 --> M1 --> N1 --> N2 --> N3
  N2 --> D1 --> D2 --> D3
  D3 -->|pass| W1
  D3 -->|fail| Q1
```
