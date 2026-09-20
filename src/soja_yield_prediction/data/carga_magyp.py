"""Carga y procesamiento del dataset de estimaciones agrícolas del MAGyP.

Este módulo contiene la lógica para leer el archivo crudo de estimaciones
agrícolas (todos los cultivos, nivel departamento) y transformarlo en un
panel provincia x campaña específico para soja 1ra y 2da.
"""

import pandas as pd

CULTIVOS_SOJA = ["soja 1ra", "soja 2da"]


def cargar_estimaciones_crudas(ruta_excel: str) -> pd.DataFrame:
    """Carga el archivo crudo de estimaciones agrícolas del MAGyP.

    Args:
        ruta_excel: Ruta al archivo .xlsx tal como fue descargado del MAGyP,
            sin ninguna modificación (nivel departamento, todos los cultivos).

    Returns:
        DataFrame con una fila por departamento, cultivo y campaña.
    """
    return pd.read_excel(ruta_excel)


def filtrar_soja(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra el dataset completo para quedarse solo con soja 1ra y 2da.

    Deliberadamente excluye la categoría "soja total", ya que es una fila
    agregada (1ra + 2da) que no aporta información independiente y
    duplicaría la señal si se incluyera junto a las otras dos.

    Args:
        df: DataFrame crudo con todos los cultivos.

    Returns:
        Subconjunto del DataFrame con cultivo en {"soja 1ra", "soja 2da"}.
    """
    return df[df["cultivo"].isin(CULTIVOS_SOJA)].copy()


def agregar_a_provincia(df_departamento: pd.DataFrame) -> pd.DataFrame:
    """Agrega datos de nivel departamento a nivel provincia.

    El rendimiento provincial se recalcula como producción total dividida
    superficie cosechada total (promedio ponderado implícito), en vez de
    promediar directamente los rendimientos departamentales. Esto evita que
    departamentos con poca superficie cosechada distorsionen el resultado
    con el mismo peso que departamentos mucho más grandes.

    Args:
        df_departamento: DataFrame a nivel departamento, ya filtrado por
            los cultivos de interés (ver `filtrar_soja`).

    Returns:
        DataFrame agregado a nivel provincia x campaña x cultivo, con
        columnas de superficie, producción y rendimiento recalculado.
    """
    df_provincial = df_departamento.groupby(
        ["provincia", "campania", "cultivo"], as_index=False
    ).agg(
        superficie_sembrada_ha=("superficie_sembrada_ha", "sum"),
        superficie_cosechada_ha=("superficie_cosechada_ha", "sum"),
        produccion_tm=("produccion_tm", "sum"),
    )

    df_provincial["rendimiento_kgxha"] = (
        df_provincial["produccion_tm"] * 1000 / df_provincial["superficie_cosechada_ha"]
    )

    return df_provincial


def cargar_soja_provincial(ruta_excel: str) -> pd.DataFrame:
    """Pipeline completo: carga, filtra y agrega el dataset de soja del MAGyP.

    Args:
        ruta_excel: Ruta al archivo crudo de estimaciones agrícolas del MAGyP.

    Returns:
        Panel provincia x campaña x cultivo (soja 1ra / soja 2da), con
        superficie, producción y rendimiento recalculado a nivel provincia.
    """
    df_crudo = cargar_estimaciones_crudas(ruta_excel)
    df_soja = filtrar_soja(df_crudo)
    return agregar_a_provincia(df_soja)
