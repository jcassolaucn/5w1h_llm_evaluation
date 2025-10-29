# Project Structure
├── data/
│   ├── basse/
│   ├── flares/
├── notebooks/
│   ├── datasets_preprocessing.ipynb
│   ├── openai_evaluator.ipynb
├── preparation/
│   ├── basse_preparation.py
│   ├── flares_preparation.py 
├── preprocessing/
│   ├── basse_preprocessing.py
│   ├── flares_preprocessing.py
├── prompts/
│   ├── evaluation_prompt.txt
├── pydantic_models/
│   ├── main_pydantic_model.py
├── results/
├── validaton/
│   ├── excel_files_ready_for_validation
│   ├── create_expert_review_task.py
│   ├── json_to_excel.py
├── requirements.txt         
├── README.md                
└── .gitignore              
└── LICENSE                 
└── .env-example            

# How to run json to excel script
python json_to_excel.py results/results_file.json result_file_for_review.xlsx
