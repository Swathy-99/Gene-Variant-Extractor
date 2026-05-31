from flask import Flask, render_template, request, send_file
import os
import csv

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/")
def home():

    vcf_folder = "vcf_files"

    if not os.path.exists(vcf_folder):
        return f"Folder not found: {vcf_folder}"

    vcf_files = []

    for file in os.listdir(vcf_folder):
        if file.endswith(".vcf"):
            vcf_files.append(file)

    return render_template(
        "index.html",
        folder_path=vcf_folder,
        files=vcf_files
    )


@app.route("/extract", methods=["POST"])
def extract():

    folder = request.form.get("folder_path")
    vcf_file = request.form.get("vcf_file")
    manual_input = request.form.get("genes_input", "").strip()
    uploaded_file = request.files.get("gene_file")

    vcf_path = os.path.join(os.getcwd(), folder, vcf_file)

    if not os.path.isfile(vcf_path):
        return f"VCF file not found: {vcf_path}"

    search_terms = []

    # Read genes from uploaded text file
    if uploaded_file and uploaded_file.filename != "":

        uploaded_path = os.path.join(
            UPLOAD_FOLDER,
            uploaded_file.filename
        )

        uploaded_file.save(uploaded_path)

        with open(uploaded_path, "r") as f:
            for line in f:
                gene = line.strip()

                if gene != "":
                    search_terms.append(gene)

        query_name = os.path.splitext(
            uploaded_file.filename
        )[0]

    # Read genes from text box
    elif manual_input != "":

        genes = manual_input.split(",")

        for gene in genes:
            gene = gene.strip()

            if gene != "":
                search_terms.append(gene)

        query_name = "_".join(search_terms[:3])

    else:
        return "Please enter genes or upload a file."

    # Clean filename
    query_name = query_name.replace(" ", "_")

    output_file = os.path.join(
        OUTPUT_FOLDER,
        f"{query_name}.csv"
    )

    header = None

    # Open VCF file
    with open(
        vcf_path,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as vcf:

        # Open output CSV file
        with open(
            output_file,
            "w",
            newline="",
            encoding="utf-8"
        ) as csv_file:

            writer = csv.writer(csv_file)

            for line in vcf:

                # Skip metadata lines
                if line.startswith("##"):
                    continue

                # Save header
                if line.startswith("#CHROM"):

                    header = line.strip().lstrip("#").split("\t")

                    writer.writerow(header)

                    continue

                # Check if any gene exists in line
                found = False

                for gene in search_terms:

                    if gene in line:
                        found = True
                        break

                # Save matching rows
                if found:
                    row = line.strip().split("\t")
                    for i in range(9,len(row)):
                        row[i] = row[i].split(":")[0]
                    writer.writerow(row)

    return send_file(output_file, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)