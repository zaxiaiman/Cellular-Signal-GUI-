import csv
import pandas as pd
import xml.etree.ElementTree as ET

input_file = "ECM512.1.nmf"
output_file = "1_cellmeas.csv"

with open(input_file, "r") as infile, open(output_file, "w", newline="") as outfile:
    writer = csv.writer(outfile)
    for line in infile:
        line = line.strip()
        if line.startswith("CELLMEAS"):
            values = line.split(",")
            writer.writerow(values)

cols_to_keep = [
    "A", "B", "L", "M", "N"
]

headers = ["Event ID", "Timestamp", "RSSI", "RSRP", "RSRQ"]

def excel_to_index(col):
    idx = 0
    for ch in col.upper():
        idx = idx * 26 + (ord(ch) - ord('A') + 1)
    return idx - 1

indices = [excel_to_index(c) for c in cols_to_keep]

input_file2 = output_file

with open(input_file2, "r") as f:
    rows = [line.strip().split(",") for line in f]

max_len = max(len(r) for r in rows)
rows_padded = [r + [""] * (max_len - len(r)) for r in rows]

df = pd.DataFrame(rows_padded)
df_filtered = df.iloc[:, indices]
df_filtered.columns = headers
df_filtered.to_csv("2_new_dataset.csv", index=False, header=False)


df2 = pd.read_csv("2_new_dataset.csv", header=None)
df2.to_csv("3_filtered_output.csv", header=headers, index=False)

df3 = pd.read_csv("3_filtered_output.csv")

def extract_mmss_csv(ts):
    parts = ts.split(":")
    mm = parts[1]
    ss = parts[2].split(".")[0]
    return f"{mm}:{ss}"

df3["mmss"] = df3["Timestamp"].apply(extract_mmss_csv)

csv_dict = {
    row["mmss"] : (row["RSSI"], row["RSRP"], row["RSRQ"])
    for _, row in df3.iterrows()
}

tree = ET.parse("ECM512.gpx")
root = tree.getroot()

ns = {"gpx": "http://www.topografix.com/GPX/1/1"}


for trkpt in root.findall(".//gpx:trkpt", ns):
    time_el = trkpt.find("gpx:time", ns)
    if time_el is None:
        continue

    gpx_time = time_el.text.replace("T", "").replace("Z", "")
    _, mm, ss = gpx_time.split(":")
    ss = ss.split(".")[0]

    mmss = f"{mm}:{ss}"

    if mmss in csv_dict:
        rssi, rsrp, rsrq = csv_dict[mmss]

        ET.SubElement(trkpt, "rssi").text = str(rssi)
        ET.SubElement(trkpt, "rsrp").text = str(rsrp)
        ET.SubElement(trkpt, "rsrq").text = str(rsrq)

def indent(elem, level=0):
    i = "\n" + level * "    "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "    "
        for child in elem:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

indent(root)
tree.write("4_ECM512_with_signal.gpx", encoding="UTF-8", xml_declaration=True)

print("Created ECM512_with_signal.gpx wiht RSSI, RSRP, RSRQ added")