from src.sources.sheets.client import GoogleSheetClient
from gspread_dataframe import get_as_dataframe, set_with_dataframe

class GoogleSheetReader:
    def __init__(self):
        self.client = GoogleSheetClient().get_client()

    def read_sheet(self, google_sheet_info: dict):
        """
        Lee una hoja de Google Sheets y devuelve un DataFrame.
        Args:
            google_sheet_info: dict
                sheet_name: str
                worksheet: str
        """
        sheet = self.client.open(google_sheet_info["sheet_name"])
        worksheet = sheet.worksheet(google_sheet_info["worksheet"])
        return get_as_dataframe(worksheet)

    def update_sheet(self, google_sheet_info: dict, clear_data: bool = False):
        """
        Actualiza una hoja de Google Sheets con los datos de un DataFrame.
        Args:
            google_sheet_info: dict
                sheet_name: str
                worksheet: str
                df: pd.DataFrame
            clear_data: bool = False
                Si es True, se limpian los datos de la hoja antes de escribir los nuevos.
                Si es False, se escriben los datos desde la ultima fila disponible.
        """
        sheet = self.client.open(google_sheet_info["sheet_name"])
        worksheet = sheet.worksheet(google_sheet_info["worksheet"])
        df = google_sheet_info["df"]

        start_row = self.start_row(worksheet, clear_data)

        if clear_data:
            worksheet.clear()
            set_with_dataframe(worksheet, df, row=start_row, col=1) # Se escribe la data desde cero
        else:
            set_with_dataframe(worksheet, df, row=start_row, col=1, include_column_header=False) # Se escribe la data desde la ultima fila sin incluir la columna
        print(f"Updated sheet: {google_sheet_info['sheet_name']}")

    def start_row(self, worksheet, clear_data: bool = False):
        """ """
        if clear_data:
            return 1
        else:
            last_row = len(worksheet.get_all_values())
            return last_row + 1 if last_row > 0 else 2