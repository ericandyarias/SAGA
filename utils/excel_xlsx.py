"""
Genera un .xlsx simple con estilos, sin librerías extra.
Excel lo abre con formato (colores, anchos, números).
"""
import zipfile
from xml.sax.saxutils import escape


def _col_letra(indice):
    letra = ""
    n = indice
    while n > 0:
        n, r = divmod(n - 1, 26)
        letra = chr(65 + r) + letra
    return letra


def _celda(fila, col, valor, estilo=0, numero=False):
    ref = f"{_col_letra(col)}{fila}"
    if numero:
        return f'<c r="{ref}" s="{estilo}" t="n"><v>{valor}</v></c>'
    texto = escape("" if valor is None else str(valor))
    return f'<c r="{ref}" s="{estilo}" t="inlineStr"><is><t>{texto}</t></is></c>'


def guardar_xlsx(ruta, filas, anchos=None, combinadas=None):
    """
    filas: lista de listas de dicts {v, s, n?} o valores simples.
    combinadas: lista de 'A1:H1'
    """
    combinadas = combinadas or []
    anchos = anchos or []

    xml_filas = []
    max_col = 1
    for i, fila in enumerate(filas, start=1):
        celdas = []
        for j, item in enumerate(fila, start=1):
            max_col = max(max_col, j)
            if isinstance(item, dict):
                celdas.append(_celda(
                    i, j, item.get("v", ""),
                    estilo=item.get("s", 0),
                    numero=bool(item.get("n"))
                ))
            else:
                celdas.append(_celda(i, j, item, 0, False))
        xml_filas.append(f'<row r="{i}">{"".join(celdas)}</row>')

    cols_xml = ""
    if anchos:
        partes = []
        for idx, ancho in enumerate(anchos, start=1):
            partes.append(f'<col min="{idx}" max="{idx}" width="{ancho}" customWidth="1"/>')
        cols_xml = "<cols>" + "".join(partes) + "</cols>"

    merges = ""
    if combinadas:
        merges = "<mergeCells count=\"{0}\">{1}</mergeCells>".format(
            len(combinadas),
            "".join(f'<mergeCell ref="{m}"/>' for m in combinadas)
        )

    sheet = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheetViews><sheetView tabSelected="1" workbookViewId="0">
<pane ySplit="8" topLeftCell="A9" activePane="bottomLeft" state="frozen"/>
</sheetView></sheetViews>
{cols_xml}
<sheetData>{"".join(xml_filas)}</sheetData>
{merges}
</worksheet>'''

    styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<numFmts count="2">
<numFmt numFmtId="164" formatCode="0"/>
<numFmt numFmtId="165" formatCode="#,##0.00"/>
</numFmts>
<fonts count="5">
<font><sz val="11"/><name val="Calibri"/></font>
<font><b/><sz val="18"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>
<font><b/><sz val="12"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>
<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>
<font><b/><sz val="11"/><color rgb="FF1B4F72"/><name val="Calibri"/></font>
</fonts>
<fills count="6">
<fill><patternFill patternType="none"/></fill>
<fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FF1B4F72"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FF117A65"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFD5F5E3"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFEAF2F8"/><bgColor indexed="64"/></patternFill></fill>
</fills>
<borders count="2">
<border><left/><right/><top/><bottom/><diagonal/></border>
<border>
<left style="thin"><color rgb="FFAED6F1"/></left>
<right style="thin"><color rgb="FFAED6F1"/></right>
<top style="thin"><color rgb="FFAED6F1"/></top>
<bottom style="thin"><color rgb="FFAED6F1"/></bottom>
<diagonal/>
</border>
</borders>
<cellStyleXfs count="1"><xf/></cellStyleXfs>
<cellXfs count="10">
<xf xfId="0"/>
<xf xfId="0" fontId="1" fillId="2" applyFont="1" applyFill="1" applyAlignment="1"><alignment horizontal="left" vertical="center"/></xf>
<xf xfId="0" fontId="2" fillId="2" applyFont="1" applyFill="1"/>
<xf xfId="0" fontId="4" applyFont="1"/>
<xf xfId="0" fontId="3" fillId="3" borderId="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" wrapText="1"/></xf>
<xf xfId="0" borderId="1" applyBorder="1"/>
<xf xfId="0" fillId="5" borderId="1" applyFill="1" applyBorder="1"/>
<xf xfId="0" fontId="4" borderId="1" applyFont="1" applyBorder="1" applyNumberFormat="1" numFmtId="165"/>
<xf xfId="0" fontId="4" fillId="5" borderId="1" applyFont="1" applyFill="1" applyBorder="1" applyNumberFormat="1" numFmtId="165"/>
<xf xfId="0" fontId="4" applyFont="1" applyNumberFormat="1" numFmtId="164"/>
</cellXfs>
</styleSheet>'''

    workbook = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Resumen ventas" sheetId="1" r:id="rId1"/></sheets>
</workbook>'''

    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>'''

    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''

    wb_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''

    with zipfile.ZipFile(ruta, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        z.writestr("xl/styles.xml", styles)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
