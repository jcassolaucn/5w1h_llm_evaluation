#!/usr/bin/env python
# coding: utf-8

# In[1]:


import json
import pandas as pd
from collections import defaultdict


# # Flares dataset
# El preprocesamiento es similar al anterior, pero para un archivo JSON que contiene una lista de objetos, cada uno con un id, text, y una lista de tags.
# Cada tag tiene un campo '5W1H_Label', 'Reliability_Label','Tag_Text' y 'Tag_Start'.

def process_flares_single_object_tags_nested_with_position(json_object):
    """
    Procesa un objeto JSON de etiquetas y anida las etiquetas procesadas
    (con enumeración y posición 'Tag_Start') dentro de una lista en el objeto resultante.
    """
    processed_object = {
        'Id': json_object.get('Id'),
        'Text': json_object.get('Text'),
        'Processed_Tags': []
    }

    tags = json_object.get('Tags', [])
    w5h1_label_counts = defaultdict(int)

    if tags:
        for tag_item in tags:
            original_w5h1_label = tag_item.get('5W1H_Label')

            processed_tag = {
                '5W1H_Label': original_w5h1_label,
                'Enumerated_Tag_Id': None,
                'Reliability_Label': tag_item.get('Reliability_Label'),
                'Tag_Text': tag_item.get('Tag_Text'),
                'Tag_Start': tag_item.get('Tag_Start')
            }

            if original_w5h1_label:
                w5h1_label_counts[original_w5h1_label] += 1
                current_count = w5h1_label_counts[original_w5h1_label]
                processed_tag['Enumerated_Tag_Id'] = f"{original_w5h1_label}_{current_count}"

            processed_object['Processed_Tags'].append(processed_tag)

    return processed_object

def get_list_of_objects_from_tags_jsonl(filepath):
    """
    Procesa un archivo JSONL (con estructura de Tags) y devuelve una lista de objetos,
    donde cada objeto contiene sus etiquetas procesadas de forma anidada y con su posición.
    """
    all_processed_objects = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for line_number, line in enumerate(f, 1):
            try:
                json_object = json.loads(line.strip())
                processed_data = process_flares_single_object_tags_nested_with_position(json_object)
                all_processed_objects.append(processed_data)
            except json.JSONDecodeError:
                print(f"Advertencia (Línea {line_number}): Se omitió una línea (etiquetas) debido a un error de decodificación JSON.")
            except Exception as e:
                print(f"Advertencia (Línea {line_number}): Se omitió una línea (etiquetas) debido a un error inesperado ({e}).")

    return all_processed_objects


# # Procesar el archivo JSONL de etiquetas y generar una lista de diccionarios.
flares_train_jsonl_file_path = '../data/flares/5w1h_subtarea_1_train.json'
flares_trial_jsonl_file_path = '../data/flares/5w1h_subtask_1_trial.json'

list_of_tagged_objects_nested_train = get_list_of_objects_from_tags_jsonl(flares_train_jsonl_file_path)
list_of_tagged_objects_nested_trial = get_list_of_objects_from_tags_jsonl(flares_trial_jsonl_file_path)

# Combinar ambos conjuntos de datos en una sola lista
flares_dataset_merged = list_of_tagged_objects_nested_train + list_of_tagged_objects_nested_trial

# Ahora 'flares_dataset_merged' es una lista de diccionarios,
# y cada diccionario tiene una clave 'Processed_Tags' con una lista de etiquetas.
# Imprime un resumen del resultado
print(f"Se procesaron {len(flares_dataset_merged)} objetos de los archivos de etiquetas.")
if flares_dataset_merged:
    print("Primer objeto de la lista de etiquetas (estructura anidada):")
    print(json.dumps(flares_dataset_merged[0], indent=2, ensure_ascii=False))


# # Filtrar y Seleccionar la Mejor Combinación por "Pirámide Invertida"
# Esta función toma la lista generada en el paso anterior y la filtra para dejar un único objeto "óptimo" por cada noticia,
# basándose en la primera etiqueta confiable de cada tipo.
def select_best_5w1h_combination(list_of_objects_with_tags):
    """
    Filtra y transforma una lista de objetos. Para cada objeto, selecciona
    la primera etiqueta 'confiable' de cada tipo 5W1H basándose en su
    posición en el texto ('Tag_Start').

    Args:
        list_of_objects_with_tags (list): La lista de objetos generada en el paso anterior.

    Returns:
        list: Una nueva lista que contiene un único objeto "óptimo" por cada
              objeto de entrada que cumplió los criterios.
    """

    best_combinations_list = []
    REQUIRED_LABELS = {'WHO', 'WHAT', 'WHEN', 'WHERE'} # Solo consideramos estas etiquetas. 'HOW' y 'WHY' son menos ocurrentes por lo que limitaría demasiado el dataset.

    for obj in list_of_objects_with_tags:
        grouped_tags = defaultdict(list)
        for tag in obj.get('Processed_Tags', []):
            label = tag.get('5W1H_Label')
            if label:
                grouped_tags[label].append(tag)

        # Primero, verificar si el objeto tiene al menos una etiqueta de cada tipo requerido
        if not REQUIRED_LABELS.issubset(grouped_tags.keys()):
            continue # Si no tiene todos los tipos, no puede ser un candidato.

        best_tags_for_this_object = []
        is_complete_with_reliable = True

        for label in REQUIRED_LABELS:
            reliable_tags = [
                tag for tag in grouped_tags[label]
                if tag.get('Reliability_Label') == 'confiable'
            ]

            if not reliable_tags:
                is_complete_with_reliable = False
                break

            reliable_tags.sort(key=lambda x: x['Tag_Start'])
            best_tag_for_label = reliable_tags[0]
            best_tags_for_this_object.append(best_tag_for_label)

        if is_complete_with_reliable:
            # Ordenar las etiquetas finales por su posición en el texto para consistencia
            best_tags_for_this_object.sort(key=lambda x: x['Tag_Start'])

            new_object = {
                'Id': obj['Id'],
                'Text': obj['Text'],
                'Processed_Tags': best_tags_for_this_object
            }
            best_combinations_list.append(new_object)

    return best_combinations_list

# 1. Llamar a la función usando la lista del paso de procesamiento como entrada.
lista_final_optima = select_best_5w1h_combination(flares_dataset_merged)

# 2. Imprime un resumen del resultado
print(f"Después de aplicar el filtro de 'mejor combinación', quedaron {len(lista_final_optima)} objetos.")

# 3. Inspeccionar el primer objeto de la lista final
if lista_final_optima:
    import json
    print("\n--- Primer objeto de la lista final ---")
    print(json.dumps(lista_final_optima[0], indent=2, ensure_ascii=False))


def flatten_optimal_objects(optimal_list):
    """
    Transforma una lista de objetos anidados a un formato plano. Extrae
    la información de 'Processed_Tags', usando '5W1H_Label' como
    la nueva clave (en formato Título) y 'Tag_Text' como su valor.

    Args:
        optimal_list (list): La lista de objetos "óptimos" generada en el
                             paso anterior.

    Returns:
        list: Una nueva lista con los objetos en formato plano.
    """

    flattened_list = []

    for obj in optimal_list:
        # Iniciar el nuevo objeto plano con los datos base.
        new_flattened_obj = {
            'Id': obj.get('Id'),
            'Text': obj.get('Text')
        }

        # Iterar a través de la lista de etiquetas ya seleccionadas.
        for tag in obj.get('Processed_Tags', []):
            label = tag.get('5W1H_Label')
            text = tag.get('Tag_Text')

            # Asegurarse de que la etiqueta tiene un tipo 5W1H.
            if label:
                # Usar el tipo de etiqueta como la nueva clave
                new_flattened_obj[label.title()] = text

        flattened_list.append(new_flattened_obj)

    return flattened_list

# Llama a la función de aplanado usando la lista del paso anterior.
lista_plana_final = flatten_optimal_objects(lista_final_optima)


# Imprime el resultado para verificar.
print(f"Se transformaron {len(lista_plana_final)} objetos a formato plano.")

if lista_plana_final:
    import json
    print("\n--- Primer objeto en el formato final plano ---")
    print(json.dumps(lista_plana_final[0], indent=2, ensure_ascii=False))


# # Crear un DataFrame de Pandas desde la lista de etiquetas procesadas para mejor visualización (opcional)
df_final = pd.DataFrame(lista_plana_final)
print("\n--- DataFrame Final ---")
df_final

