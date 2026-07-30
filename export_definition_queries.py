import csv
import os

import arcpy


def _is_data_layer(layer):
    if getattr(layer, "isGroupLayer", False):
        return False
    try:
        return layer.supports("DEFINITIONQUERY")
    except Exception:
        return False


def _list_layer_definition_queries(layer):
    queries = []
    try:
        query_items = layer.listDefinitionQueries() or []
    except Exception:
        query_items = []

    for item in query_items:
        title = item.get("name", "")
        sql = item.get("sql", "")
        is_active = bool(item.get("isActive", False))
        queries.append((title, sql, is_active))

    if queries:
        return queries

    fallback_sql = getattr(layer, "definitionQuery", "") or ""
    if fallback_sql:
        return [("", fallback_sql, True)]
    return [("", "", False)]


def export_definition_queries(aprx_path, map_name, output_csv):
    aprx = arcpy.mp.ArcGISProject(aprx_path)
    maps = aprx.listMaps(map_name)
    if not maps:
        raise ValueError(f"Map '{map_name}' was not found in '{aprx_path}'.")
    map_obj = maps[0]

    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)

    with open(output_csv, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            ["map_name", "layer_name", "query_title", "definition_query", "is_active"]
        )

        for layer in map_obj.listLayers():
            if not _is_data_layer(layer):
                continue

            for title, sql, is_active in _list_layer_definition_queries(layer):
                writer.writerow([map_obj.name, layer.name, title, sql, is_active])

    arcpy.AddMessage(f"Definition query report written to: {output_csv}")


def _run_as_tool():
    aprx_path = arcpy.GetParameterAsText(0)
    map_name = arcpy.GetParameterAsText(1)
    output_csv = arcpy.GetParameterAsText(2)
    export_definition_queries(aprx_path, map_name, output_csv)


if __name__ == "__main__":
    _run_as_tool()
