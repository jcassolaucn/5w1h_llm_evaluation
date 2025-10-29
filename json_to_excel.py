import pandas as pd
import json
import argparse


def create_excel_for_review(json_path: str, excel_path: str):
    """
    Converts a JSON file with review tasks into a formatted Excel file
    to facilitate the experts' work.

    Args:
        json_path (str): Path to the input JSON file.
        excel_path (str): Path where the output Excel file will be saved.
    """
    print(f"Loading data from '{json_path}'...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at path: {json_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: The file '{json_path}' is not a valid JSON.")
        return

    # Flatten the JSON structure to convert it into a table
    rows_for_excel = []
    for task in json_data:
        # Common information repeated across the 6 rows for each task
        common_info = {
            'doc_id': task['document_info']['doc_id'],
            'model_evaluated': task['extraction_info']['model_evaluated'],
            'full_source_text': task['document_info']['full_source_text'],
            'extraction_to_evaluate': task['extraction_info']['extraction_to_evaluate'],
            'confidence_level': task['confidence_level']['score'],
            'confidence_level_justification': task['confidence_level']['justification'],
        }

        # Create one row per criterion to be evaluated
        for criterion, details in task['judgments_to_review'].items():
            row = {
                'review_id': f"{task['review_id']}_{criterion}",
                'criterion': criterion,
                'ai_score': details['ai_score'],
                'ai_justification': details['ai_justification'],
                **common_info,
                # Empty fields for the expert to fill in
                'expert_score_validity (1-5)': '',
                'expert_explanation_quality': '',
                'expert_optional_notes': '',
            }
            rows_for_excel.append(row)

    if not rows_for_excel:
        print("No data found to process in the JSON file.")
        return

    # Create a pandas DataFrame
    df = pd.DataFrame(rows_for_excel)

    # Reorder columns for a more logical structure
    column_order = [
        'review_id', 'doc_id', 'model_evaluated',
        'confidence_level', 'confidence_level_justification',
        'criterion', 'ai_score', 'ai_justification',
        'expert_score_validity (1-5)', 'expert_explanation_quality', 'expert_optional_notes',
        'full_source_text', 'extraction_to_evaluate'
    ]
    df = df[column_order]

    print(f"Creating Excel file at '{excel_path}'...")

    # Use XlsxWriter to add advanced formatting to the Excel file. Make sure to install it via pip if not already installed.
    with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Review Tasks', index=False)

        workbook = writer.book
        worksheet = writer.sheets['Review Tasks']

        # 1. Adjust column widths
        worksheet.set_column('A:A', 40)  # review_id
        worksheet.set_column('B:B', 30)  # doc_id
        worksheet.set_column('C:D', 25)  # model, criterion
        worksheet.set_column('E:E', 10)  # ai_score
        worksheet.set_column('F:F', 50)  # ai_justification
        worksheet.set_column('G:G', 25)  # expert_score_validity
        worksheet.set_column('H:H', 28)  # expert_explanation_quality
        worksheet.set_column('I:I', 50)  # expert_optional_notes
        worksheet.set_column('J:K', 50)  # source_text, extraction
        worksheet.set_column('L:L', 15)  # confidence_level
        worksheet.set_column('M:M', 50)  # confidence_level_justification

        # 2. Create a drop-down menu for 'expert_explanation_quality'
        quality_options = ['Precisa y Útil', 'Plausible pero Imprecisa', 'Incorrecta o No Útil']
        worksheet.data_validation('H2:H{}'.format(len(df) + 1), {
            'validate': 'list',
            'source': quality_options
        })

        # 3. Header formatting
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # 4. Freeze the top row (headers)
        worksheet.freeze_panes(1, 0)

    print("Process completed successfully!")


if __name__ == "__main__":
    # Configure the command-line argument parser
    parser = argparse.ArgumentParser(
        description="Converts a JSON file with review tasks into a formatted Excel file."
    )
    parser.add_argument(
        "json_input",
        help="Path to the input JSON file (e.g., expert_review_tasks.json)"
    )
    parser.add_argument(
        "excel_output",
        help="Path to the output Excel file (e.g., journalists_review.xlsx)"
    )

    args = parser.parse_args()

    # Execute the main function
    create_excel_for_review(args.json_input, args.excel_output)
