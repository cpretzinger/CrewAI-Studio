# pg_export_crew.py

import streamlit as st
from streamlit import session_state as ss
from my_crew import MyCrew
from my_agent import MyAgent
from my_task import MyTask
from base_tool import MyTool as Tool
import db_utils
import os
import json
import shutil
import traceback

class PageExportCrew:
    def __init__(self):
        self.name = "Export/Import Crew"
        self.maintain_session_state()

    @staticmethod
    def maintain_session_state():
        """Initialize default session state variables if they don't exist."""
        if 'crews' not in ss:
            ss.crews = db_utils.load_crews()  # Ensure this loads a list of MyCrew instances

    def export_crew_data(self):
        """Exports all crew data to a JSON file and provides a download link."""
        crew_data = [crew.to_dict() for crew in ss.crews]

        json_str = json.dumps(crew_data, indent=4)
        st.download_button(
            label="Download Crew Data as JSON",
            data=json_str,
            file_name="crew_export.json",
            mime="application/json"
        )
        st.success("Crew data is ready for download.")

    def prepare_export(self):
        """
        Creates a zip file containing crew data and any supplementary files.
        Provides a download link for the zip archive.
        """
        export_dir = "export_temp"
        os.makedirs(export_dir, exist_ok=True)

        # Export each crew's data into individual JSON files within the export directory
        for crew in ss.crews:
            crew_folder = os.path.join(export_dir, crew.name)
            os.makedirs(crew_folder, exist_ok=True)
            crew_file_path = os.path.join(crew_folder, f"{crew.name}.json")
            with open(crew_file_path, "w") as f:
                json.dump(crew.to_dict(), f, indent=4)

            # If there are supplementary files (e.g., tools, logs), include them here
            # Example:
            # supplementary_file = os.path.join(crew_folder, "supplementary.txt")
            # with open(supplementary_file, "w") as f:
            #     f.write("Supplementary information")

        # Create a zip archive of the export directory
        shutil.make_archive("crew_export", 'zip', export_dir)
        shutil.rmtree(export_dir)  # Clean up temporary folder

        # Read the zip file and provide it for download
        with open("crew_export.zip", "rb") as f:
            zip_bytes = f.read()

        st.download_button(
            label="Download Crew Export as Zip",
            data=zip_bytes,
            file_name="crew_export.zip",
            mime="application/zip"
        )
        st.success("Export archive is ready for download.")

        # Optionally, remove the zip file after offering it for download
        os.remove("crew_export.zip")

    def import_crew_data(self, uploaded_file):
        """Imports crew data from an uploaded JSON file and updates session state."""
        try:
            crew_data = json.load(uploaded_file)
            imported_crews = []

            for crew_info in crew_data:
                crew = MyCrew.from_dict(crew_info)
                imported_crews.append(crew)

            # Optionally, merge with existing crews or replace
            # Here, we choose to append imported crews to existing ones
            if 'crews' not in ss:
                ss.crews = []
            ss.crews.extend(imported_crews)
            db_utils.save_crews(ss.crews)  # Save the updated crews to the database
            st.success("Crew data imported successfully.")
            st.experimental_rerun()  # Refresh the UI to show updates
        except json.JSONDecodeError:
            st.error("Invalid JSON file. Please upload a valid JSON.")
        except Exception as e:
            st.error(f"An error occurred during import: {e}")
            st.text(traceback.format_exc())

    def import_crew_zip(self, uploaded_file):
        """Imports crew data from an uploaded zip file containing JSON crew files."""
        try:
            # Extract zip contents to a temporary directory
            temp_zip_path = os.path.join("import_temp", "crew_import.zip")
            os.makedirs("import_temp", exist_ok=True)
            with open(temp_zip_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            shutil.unpack_archive(temp_zip_path, "import_temp", 'zip')
            imported_crews = []
            for root, dirs, files in os.walk("import_temp"):
                for file in files:
                    if file.endswith(".json"):
                        file_path = os.path.join(root, file)
                        with open(file_path, "r") as f:
                            crew_info = json.load(f)
                            crew = MyCrew.from_dict(crew_info)
                            imported_crews.append(crew)

            # Clean up temporary directory
            shutil.rmtree("import_temp")

            # Append imported crews to session state
            if 'crews' not in ss:
                ss.crews = []
            ss.crews.extend(imported_crews)
            db_utils.save_crews(ss.crews)  # Save the updated crews to the database

            st.success("Crew data imported successfully from zip.")
            st.experimental_rerun()  # Refresh the UI to show updates
        except shutil.ReadError:
            st.error("Invalid zip file. Please upload a valid zip containing JSON files.")
        except json.JSONDecodeError:
            st.error("One or more JSON files in the zip are invalid.")
        except Exception as e:
            st.error(f"An error occurred during import: {e}")
            st.text(traceback.format_exc())

    def draw(self):
        """Displays the UI for export and import options."""
        st.subheader(self.name)
        st.write("### Export Crews")
        export_options = ["Export All Crews as JSON", "Export All Crews as Zip"]
        export_choice = st.selectbox("Choose export format", export_options)

        if export_choice == "Export All Crews as JSON":
            self.export_crew_data()
        elif export_choice == "Export All Crews as Zip":
            self.prepare_export()

        st.write("---")
        st.write("### Import Crews")
        import_choice = st.selectbox("Choose import format", ["Import Crews from JSON", "Import Crews from Zip"])

        if import_choice == "Import Crews from JSON":
            uploaded_file = st.file_uploader("Choose a JSON file to import crew data", type="json")
            if uploaded_file:
                if st.button("Import Crew Data"):
                    self.import_crew_data(uploaded_file)
        elif import_choice == "Import Crews from Zip":
            uploaded_zip = st.file_uploader("Choose a Zip file to import crew data", type="zip")
            if uploaded_zip:
                if st.button("Import Crew Data from Zip"):
                    self.import_crew_zip(uploaded_zip)

        st.write("---")
        st.write("### Current Crews")
        if 'crews' in ss and ss.crews:
            for crew in ss.crews:
                crew.draw()
        else:
            st.warning("No crews available to display.")

# Instantiate and render the page
def main():
    page = PageExportCrew()
    page.draw()

if __name__ == "__main__":
    main()
