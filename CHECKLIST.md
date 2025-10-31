# Retention Intelligence System - Development Checklist

## ✅ Phase 1: Project Setup (COMPLETED)

### Structure
- [x] Create project directory structure
- [x] Setup config directory with config.yaml
- [x] Create .gitignore for sensitive data
- [x] Create requirements.txt with dependencies
- [x] Setup SQL directories (schemas, marts, views, procedures)
- [x] Setup Python src structure (utils, data_engineering, features, models, scoring, monitoring)
- [x] Create notebooks directory
- [x] Create scripts directory
- [x] Create docs directory

### Database Connectors
- [x] PostgreSQL connector (psycopg2 + SQLAlchemy)
- [x] MongoDB connector (pymongo)
- [x] Database connection context managers
- [x] Error handling for connections

### Core Modules
- [x] Logger setup (console + file handlers)
- [x] MongoExtractor class for data extraction
- [x] PostgresLoader class for data loading
- [x] Schema exploration utilities

### SQL Templates
- [x] Schema creation script (01_create_schema.sql)
- [x] Core user table template (02_core_user_template.sql)
- [ ] Other table DDL scripts (TODO after MongoDB exploration)

### Scripts
- [x] explore_mongo.py - MongoDB exploration script
- [x] setup_postgres.py - PostgreSQL setup script
- [ ] build_marts.py - Mart building script (TODO)
- [ ] train_model.py - Model training script (TODO)
- [ ] generate_scores.py - Scoring script (TODO)

### Notebooks
- [x] 01_mongo_exploration.ipynb - MongoDB exploration notebook
- [ ] 02_eda_users.ipynb - User EDA (TODO)
- [ ] 03_eda_behavior.ipynb - Behavior EDA (TODO)
- [ ] 04_feature_engineering.ipynb - Feature engineering (TODO)
- [ ] 05_baseline_models.ipynb - Baseline models (TODO)
- [ ] 06_advanced_models.ipynb - Advanced models (TODO)

### Documentation
- [x] README.md - Project overview with badges and roadmap
- [x] SETUP_SUMMARY.md - Quick reference and summary
- [x] PROJECT_STRUCTURE.md - Detailed structure explanation
- [x] GETTING_STARTED.md - Step-by-step getting started guide
- [x] CHECKLIST.md - This file

---

## 🔄 Phase 2: Data Discovery (CURRENT PHASE)

### MongoDB Exploration
- [ ] Run `python scripts/explore_mongo.py`
- [ ] List all MongoDB collections
- [ ] Explore schema of user collection
- [ ] Explore schema of HeroPass/subscription collection
- [ ] Explore schema of sessions/workouts collection
- [ ] Explore schema of inBody/assessment collection
- [ ] Save all schemas to `data/schemas/` as JSON

### Data Mapping
- [ ] Create mapping document: MongoDB fields → RIS tables
- [ ] Identify which internal factors (27) are available
- [ ] Identify which external factors (30+) are available
- [ ] Identify derived fields that need calculation
- [ ] Identify missing fields that need assumptions

### Understanding Business Logic
- [ ] Understand HeroPass purchase flow
- [ ] Understand how to identify renewals
- [ ] Understand freeze mechanism
- [ ] Understand cancellation/missed sessions logic
- [ ] Document business rules

### SQL Schema Finalization
- [ ] Finalize ris.core_user DDL
- [ ] Create ris.core_hp_period DDL
- [ ] Create ris.fact_user_week DDL
- [ ] Create ris.label_hp DDL
- [ ] Create ris.interval_hp DDL
- [ ] Create ris.ref_calendar DDL
- [ ] Create meta tables DDL
- [ ] Review all constraints and indexes

---

## ⏳ Phase 3: Data Engineering

### PostgreSQL Setup
- [ ] Run `python scripts/setup_postgres.py`
- [ ] Verify all tables created successfully
- [ ] Populate ris.ref_calendar with date range
- [ ] Add holidays to ref_calendar
- [ ] Create initial model_bands entries

### ETL Pipeline
- [ ] Write MongoDB → PostgreSQL ETL for users
- [ ] Write MongoDB → PostgreSQL ETL for HeroPass periods
- [ ] Write MongoDB → PostgreSQL ETL for sessions
- [ ] Write MongoDB → PostgreSQL ETL for assessments/inBody
- [ ] Create initial data load script
- [ ] Test ETL pipeline with sample data

### Feature Calculation
- [ ] Calculate user baseline metrics (engagement_baseline, sessions_per_week_baseline, etc.)
- [ ] Populate ris.core_user with internal factors
- [ ] Calculate weekly aggregates for ris.fact_user_week
- [ ] Calculate EWMA baselines for each user
- [ ] Calculate deltas from baseline
- [ ] Populate ris.label_hp with targets

### Data Quality
- [ ] Write data quality checks
- [ ] Check for missing values
- [ ] Check for outliers
- [ ] Validate foreign keys
- [ ] Generate DQ report
- [ ] Populate ris.dq_feature_stats

---

## ⏳ Phase 4: EDA & Feature Engineering

### User Analysis
- [ ] Demographics distribution (age, gender, location)
- [ ] HeroPass type distribution
- [ ] Onboarding analysis (trial vs non-trial, referral vs individual)
- [ ] Club distribution
- [ ] Cohort analysis

### Behavior Analysis
- [ ] Session frequency distribution
- [ ] Completion rate analysis
- [ ] Cancellation patterns
- [ ] Time-of-day preferences
- [ ] Booking patterns
- [ ] Freeze behavior analysis

### Retention Analysis
- [ ] Overall retention rates (30d, 60d, 90d)
- [ ] Retention by cohort
- [ ] Retention by HeroPass type
- [ ] Retention by demographics
- [ ] Survival curves

### Feature Engineering
- [ ] Create composite engagement score
- [ ] Create risk scores for each factor
- [ ] Engineer interaction features
- [ ] Create time-based features (days since last session, etc.)
- [ ] Encode categorical variables
- [ ] Scale numerical features

### Feature Selection
- [ ] Correlation analysis
- [ ] Multicollinearity check (VIF)
- [ ] Feature importance (Random Forest)
- [ ] Recursive feature elimination
- [ ] Select final feature set

### Populate Meta Tables
- [ ] Populate ris.meta_feature_catalog with all features
- [ ] Document feature calculation logic
- [ ] Document data sources

---

## ⏳ Phase 5: Modeling

### Data Split
- [ ] Define train/validation/test strategy
- [ ] Temporal split (time-based)
- [ ] Stratified by renewal outcome
- [ ] Handle class imbalance (SMOTE, undersampling, or class weights)

### Baseline Models
- [ ] Logistic Regression (30d target)
- [ ] Logistic Regression (60d target)
- [ ] Logistic Regression (90d target)
- [ ] Random Forest baseline
- [ ] Evaluate with ROC-AUC, PR-AUC, Brier score

### Advanced Models
- [ ] XGBoost
- [ ] LightGBM
- [ ] CatBoost
- [ ] Hyperparameter tuning (Optuna)
- [ ] Cross-validation
- [ ] Evaluate all models

### Survival Analysis
- [ ] Cox Proportional Hazards
- [ ] Accelerated Failure Time (AFT)
- [ ] Discrete-time survival (weekly intervals)
- [ ] Evaluate concordance index

### Ensemble
- [ ] Stacking ensemble
- [ ] Blending
- [ ] Final model selection

### Model Interpretation
- [ ] Feature importance (SHAP)
- [ ] Partial dependence plots
- [ ] Individual explanations
- [ ] Risk factor identification

### Model Documentation
- [ ] Create model cards
- [ ] Document training process
- [ ] Document evaluation metrics
- [ ] Save models to MLflow

### Populate Model Tables
- [ ] Populate ris.model_importance
- [ ] Populate ris.model_calibration
- [ ] Document model versions

---

## ⏳ Phase 6: Production

### Scoring Pipeline
- [ ] Write batch scoring script
- [ ] Score all active users
- [ ] Assign risk bands
- [ ] Identify top risk factors per user
- [ ] Populate ris.model_scores_daily

### Monitoring
- [ ] Setup feature drift monitoring
- [ ] Setup prediction drift monitoring
- [ ] Setup model performance monitoring
- [ ] Create alerting rules

### Retraining
- [ ] Define retraining schedule
- [ ] Automate retraining pipeline
- [ ] Automate model evaluation
- [ ] Automate model deployment

### Reporting
- [ ] Daily risk report (users by risk band)
- [ ] Weekly retention forecast
- [ ] Model performance dashboard
- [ ] Feature drift report

### API (Optional)
- [ ] Create FastAPI endpoints
- [ ] Real-time scoring endpoint
- [ ] Batch scoring endpoint
- [ ] Model info endpoint
- [ ] Deploy API

### Documentation
- [ ] Runbook for scoring
- [ ] Runbook for retraining
- [ ] Runbook for monitoring
- [ ] API documentation

---

## 📋 Key Milestones

| Milestone | Status | Expected Completion |
|-----------|--------|---------------------|
| Project Setup | ✅ DONE | - |
| MongoDB Exploration | 🔄 IN PROGRESS | TBD |
| Data Mapping | ⏳ TODO | TBD |
| PostgreSQL Vitrine Creation | ⏳ TODO | TBD |
| ETL Pipeline | ⏳ TODO | TBD |
| EDA | ⏳ TODO | TBD |
| Feature Engineering | ⏳ TODO | TBD |
| Baseline Model | ⏳ TODO | TBD |
| Advanced Models | ⏳ TODO | TBD |
| Production Scoring | ⏳ TODO | TBD |

---

## 🎯 Next Action Items

1. **IMMEDIATE**: Run `python scripts/explore_mongo.py`
2. Document MongoDB schema findings
3. Create MongoDB → PostgreSQL mapping document
4. Finalize SQL DDL scripts based on MongoDB structure
5. Run `python scripts/setup_postgres.py`

---

## 📝 Notes

- Remember to update `.env` with actual credentials before running any scripts
- All data files should go in `data/` (excluded from git)
- All model files should go in `models/` (excluded from git)
- Log all major operations to `logs/` for debugging
- Use `config/config.yaml` for all configuration parameters

---

## 🔗 Quick Links

- [README.md](README.md) - Project overview
- [SETUP_SUMMARY.md](SETUP_SUMMARY.md) - Quick summary
- [GETTING_STARTED.md](docs/GETTING_STARTED.md) - Detailed guide
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Structure details
- [config/config.yaml](config/config.yaml) - Configuration

---

**Last Updated**: 2025-10-30
