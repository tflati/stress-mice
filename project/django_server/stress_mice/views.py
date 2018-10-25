from django.shortcuts import render
from django.http import HttpResponse
import json
import os
import sys
import glob

from collections import Counter

from decimal import Decimal

import rpy2
import rpy2.robjects as robjects
import rpy2.robjects.packages as rpackages
import datetime
from django.core.cache import cache
from django.conf.locale import bg

def create_new_image(url, width="100px"):
    return {
            "type": "image",
            "data": {
                "url": url,
                "width": width
            }
        }
def create_new_paragraph(text, inline=False):
    return {
        "type": "paragraph",
        "data": {
            "value": text
        },
        "inline": inline
    }
    
def create_new_text(text, inline=False, tooltip=None):
    t = {
        "type": "text",
        "label": text
    }
    
    if tooltip is not None:
        t["title"] = tooltip
    
    return t
    
def create_new_link(url, text, tooltip="", target="_blank"):
    return {
        "type": "link",
        "title": tooltip,
        "target": target,
        "url": url,
        "label": text
    }

def create_linkable_image(img_url, target_url, tooltip="", width="100px"):
    return {
        "type": "linkable_image",
        "data": {
            "title": tooltip,
            "width": width,
            "url": img_url,
            "link": target_url
        }
    }

def create_select(data, key, label, value=None, url=None, tooltip=""):
    select = {
        "type": "select",
        "key": key,
        "layout": "row",
        "layout_align": "start start",
        "subtype": "form",
        "data": {},
        "subdata": [
        ]
    }
    
    if label != None:
        select["label"] = label
    
    if value != None:
        select["data"]["value"] = value
    
    for x in data:
        select["subdata"].append(x)
    
    return select
    
def create_new_button(text, url = None, action="link", tooltip=None, img=None, img_height=None, icon=None, icon_color=None, icon_modifiers=None, color=None):
    button =  {
        "type": "button",
        "action": action,
        "label": text,
        "data": {}
    }
    
    if url is not None:
        button["data"]["url"] = url
        button["data"]["target"] = "_blank"
    
    if color is not None:
        button["color"] = color
    
    if tooltip is not None:
        button["title"] = tooltip
    
    if img is not None:
        button["data"]["image"] = img
        if img_height is not None: button["data"]["height"] = img_height
        
    if icon is not None:
        button["data"]["icon"] = icon
        if icon_color is not None: button["data"]["color"] = icon_color
        if icon_modifiers is not None: button["data"]["modifiers"] = icon_modifiers
        
    
    return button
    
def create_new_multi_element(layout=None, alignment=None):
    multi = {
        "type": "multi",
        "elements": []
    }
    
    if layout is not None: multi["layout"] = layout
    if alignment is not None: multi["layout_align"] = alignment
    
    return multi
    
def add_element_to_multi_element(multielement, element):
    multielement["elements"].append(element)

def create_new_select(label, key, required=True, data_url = None, data = None):
    
    if data_url is None and data is None: return None
    
    select = {
        "label": label,
        "type":"select",
        "subtype":"form",
        "required": required,
        "data": {}
    }
    
    if key is not None:
        select["key"] = key
        
        select["data"]["onChange"] = {
            "key": key,
            "action": "write"
        }
    
    if data_url is not None:
        select["data"]["url"] = data_url
    
    if data is not None:
        select["subdata"] = data
    
    return select

def create_table():
    return {"structure": {"field_list": []}, "total": 0, "hits": []}

def create_header_col(label, title = None, tooltip = None, filter_title = None):
    
    if title is None: title = label
    if tooltip is None: tooltip = label
    if filter_title is None: filter_title = label + " filters:"
    
    return {
        "label": label,
        "title": title,
        "tooltip": tooltip,
        "filters": {
            "title": filter_title,
            "list": []
        }
    }

def add_header(table, header):
    table["structure"]["field_list"] = header

def get_table_length(table):
    return len(table["hits"])

def create_row(table):
    row = {}
    for col in table["structure"]["field_list"]:
        row[col["title"]] = []
        
    return row

def add_row(table, row):
    table["hits"].append(row)

def create_chart(type, url=None, data=None, min=None, xaxis="", width="100", descriptions=[]):
    
    chart = {
        "type": type,
        "data": {
            "width": width
        }
    }
    
    if url is None and data is None: return chart
    
    if url is not None:
        chart["data"]["url"] = url
    
    chart_data = [[{"label": key}, value, {"id": str(xaxis) + "_" + str(value)}] for (key, value) in data]
    
    if data is not None:
        chart["subdata"] = {"header": [xaxis, "Number"], "items": chart_data, "descriptions": descriptions}
        
    if min is not None:
        chart["data"]["min"] = min
        
    return chart
    

def convert_bytes(number):
    if number is None: return "Unknown size"
        
    sizes = ["B", "KB", "MB", "GB", "TB"]
    s = float(number)
    i = 0;
    while s >= 1024 and i < len(sizes):
        s = s / 1024
        i += 1

    #return "{0:.2f} {}".format(s, sizes[i])
    return "{0:.2f}".format(s) + " " + sizes[i]

BASE_BGE_DIR = os.path.dirname(__file__) + "/Ballgown_Extractor/"
BASE_DATA_DIR = os.path.dirname(__file__) + "/data/"















def load_dataset_info():
    filename = BASE_DATA_DIR + "project.json"
    dataset = json.loads(open(filename, "r").read())
    
    map = {}
    for bioproject in dataset["projects"]:
        bioproject_id = bioproject["id"]
        
        # Bioprojects skipped/removed by Arianna
        if bioproject_id == "PRJNA341670": continue
        if bioproject_id == "PRJNA392171": continue
        
        if bioproject_id not in map:
            map[bioproject_id] = {
                    "size": 0,
                    "organism": None,
                    "experiments": 0,
                    "paper_id": set(),
                    "platform": set(),
                    "samples": 0,
                }
        data = map[bioproject_id]
        
        data["paper_id"] = bioproject["papers"]
        
        for experiment in bioproject["experiments"]:
            data["experiments"] += 1
            dataset = experiment["dataset"]
            size = dataset["size"]
            organism = dataset["genome"]
            paper_id = dataset["paper_id"] if "paper_id" in dataset else None
            platform = dataset["platform"]
            samples = len(dataset["sample_ids"])
            
            data["size"] += size
#             if paper_id is not None: data["paper_id"].add(paper_id)
            data["platform"].add(platform)
            data["samples"] += samples
            data["organism"] = organism
            
    return map

# Create your views here.
def dataset_overview(request):
    
    map = load_dataset_info()
    
    rows = []
    for bioproject_id in map:
        data = map[bioproject_id]
        print("DATA", data)
        row = []
        
        row.append(create_new_link("https://www.ncbi.nlm.nih.gov/bioproject/" + bioproject_id, bioproject_id, tooltip="See this BioProject within NCBI ("+bioproject_id+")"))
        row.append(create_new_text(data["samples"]))
        
        row.append(create_new_text(data["experiments"]))
        row.append(create_new_text(convert_bytes(data["size"])))
        row.append(create_new_text(data["organism"]))
        
        paper_cell = create_new_multi_element(layout="row")
        
        if data["paper_id"]:
            
            for paper in data["paper_id"]:
                tooltip = "See this paper in NCBI (ID="+paper["id"]+")" if paper["source"] == "automatic" else "Open the PDF file '"+paper["url"].split("/")[-1]+"'"
                image_url = "imgs/pdf.png" if paper["source"] == "manual" else "imgs/pubmed.jpg"
                width = 50 if paper["source"] == "manual" else 75
                add_element_to_multi_element(paper_cell, create_linkable_image(image_url, paper["url"], width=str(width)+"px", tooltip=tooltip))
        else:
            add_element_to_multi_element(paper_cell, create_new_text("No paper available"))
        
        row.append(paper_cell)
            
        platforms = []
        for platform in data["platform"]:
            platforms.append(create_new_text(platform))
        row.append(platforms[0])

        row.append(create_new_button("See detail", url="bioproject/"+ bioproject_id))
        row.append(create_linkable_image(img_url="imgs/download.png", target_url="data/phenodata/"+ bioproject_id + "/phenodata.csv", width="35px", tooltip="Download the phenodata in CSV format for bioproject " + bioproject_id))

        rows.append(row)
    
    header = ["BioProject ID", "Number of samples", "Experiments", "Size", "Organism", "Paper ID", "Platform", "Details", "Phenodata download"]
    response = {"total": len(rows), "header": header, "items": rows}
    
    return HttpResponse(json.dumps(response))




def clear_cache(request):
    cache.clear()
    return HttpResponse("OK")

import threading
lock = threading.Lock()

def init():
    
    base = rpackages.importr("base")
    base.source(BASE_BGE_DIR + "definitions.R")
    
    return base

def get_header():
    return [
        {
            "label": "result_id",
            "title": "Result ID",
            "tooltip": "Result ID",
            "filters": {
                "title": "Result ID filters:",
                "list": [
                    {
                        "type": "select",
                        "key": "result_id",
                        "title": "Select a result ID:",
                        "placeholder": "",
                        "operators": "LIKE",
                        "chosen_value": ""
                    }
                ]
            }
        },
        {
            "label": "gene",
            "title": "Coverage",
            "tooltip": "Gene symbol",
            "filters": {
                "title": "gene symbol filters:",
                "list": [
                    {
                        "type": "select",
                        "key": "gene_symbol",
                        "title": "Select a gene symbol:",
                        "placeholder": "",
                        "operators": "LIKE",
                        "chosen_value": ""
                    }
                ]
            }
        },
        {
            "label": "geneID",
            "title": "FPKM",
            "tooltip": "gene ID",
            "filters": {
                "title": "Gene ID filters:",
                "list": [
                    {
                        "type": "select",
                        "key": "geneID",
                        "title": "Select a gene ID:",
                        "placeholder": "",
                        "operators": "LIKE",
                        "chosen_value": ""
                    }
                ]
            }
        }
    ]
    
def get_combinations(request):
    combinations_path = BASE_DATA_DIR + "/" + "combinations.tsv"
    
    data = json.loads(request.body.decode('utf-8'))
    print(data)
    
    multielement = create_new_multi_element()
#     multielement["subtype"] = "form"
    multielement["layout"] = "column"
    multielement["layout_align"] = "start start"
    
    items = []
    for k,v in data.items():
        if k.startswith("condition"):
            o = int(k.replace("condition", ""))
            items.append({"order": o, "key": k, "value": v})
    items.sort(key=lambda x: x["order"])   
    
    to_remove = set()
    for item in items:
        v = item["value"]
        select = create_new_select("Selection", item["key"], data = [{"id": v, "label": v, "img": "imgs/covariate.png"}])
        select["data"]["value"] = {"id": v, "label": v, "img": "imgs/covariate.png"}
        add_element_to_multi_element(multielement, select)
        to_remove.add(v)
    
    options = set()
    options2values = {}
    with open(combinations_path, "r") as file:
        for line in file:
            
            combination_id, bioproject, condition, covariate, dimensions = line.strip().split("\t")
                                    
            columns = dimensions.split("|")
            for col in columns:
                if col in to_remove: continue
                options.add(col)
                if col not in options2values:
                    options2values[col] = set()

            condition_formula = selector.parse_condition(selector.tokenize(condition))
            for leaf in condition_formula.get_leaves():
                if selector.get_operator(leaf) is None: continue
                key, value = leaf.split(selector.get_operator(leaf))
                options2values[key].add(value.replace("\"", ""))
    
    if options:
        for option in sorted(options):
            values = list(options2values[option])
            values.sort()
            print("OPTION", option, "VALUES", values)
            if not values: continue
            
            option_object = create_new_text(option + " = ")
            select = create_new_select(option, option, data = [{"id": x, "label": x, "img": "imgs/covariate.png"} for x in values])
            
            row = create_new_multi_element()
#             row["subtype"] = "form"
            add_element_to_multi_element(row, option_object)
            add_element_to_multi_element(row, select)
            
            add_element_to_multi_element(multielement, row)
            
    button = create_new_button("Submit", action="nothing")
    button["key"] = "submit"
    button["type"] = "submit"
    button["subtype"] = "form"
    button["data"]["source"] = "selection_result"
    button["data"]["onClick"] = [
            {
                "action": "write",
                "key": "search_started",
                "value": True
            }
        ]
    add_element_to_multi_element(multielement, button)
    
    return HttpResponse(json.dumps(multielement))

def get_differential_expression(request):
    data = json.loads(request.body.decode('utf-8'))
    print(data)
#     data = {"Region": "hipp"}

    offset = 0
    limit = 10
    
    if "offset" in data: offset = data["offset"]
    if "limit" in data: limit = data["limit"]
    
    result = create_table()
    header = []
    header.append(create_header_col("Gene ID"))
    header.append(create_header_col("Score"))
    header.append(create_header_col("Supporting bioprojects"))
    add_header(result, header)
    
    for key,value in data.items():
        print(key, value)
        if value is not None:
            relative_path = "diff/{}={}/out_gene/distribution.txt".format(key, value)
            filepath = BASE_DATA_DIR + relative_path
            print("File: ", filepath)
            if not os.path.exists(filepath): continue
            
            n = 0
            with open(filepath) as file:
                for line in file:
                    n += 1
                    if n < offset: continue
                    
                    row = create_row(result)
                    if get_table_length(result) > limit: continue
                    
                    for i,field in enumerate(line.strip().split("\t")):
                        if i == 2:
                            for f in field.split("|"):
                                button = create_new_button(f, url="/stress_mice_api/stress_mice/differential_expression_file", tooltip="See the list of genes/transcripts for this configuration")
                                button["items"] = [create_new_text(f)]
                                button["data"]["value"] = relative_path
                                button["data"]["onClick"] = [{
                                        "key": "expression_file",
                                        "action": "write",
                                        "scope": "global"
                                    }]
                                
                                row[header[i]["title"]].append(button)
                        else:
                            cell = create_new_text(field)
                            row[header[i]["title"]].append(cell)
                        
                    add_row(result, row)
                    
            result["total"] = n
    
    return HttpResponse(json.dumps(result))

def get_differential_expression_file(request):
    result = {}
    return HttpResponse(json.dumps(result))

def get_dataset_phenotypic_information(request):
    result = create_new_multi_element("column", "start center")
    
    files = [x for x in glob.glob(BASE_DATA_DIR + "/phenotypic_information/*")]
    ordering = {}
    for x in files:
        simple_name = x.split("/")[-1].replace(".csv.png", "")
        ordering[x] = \
            0 if simple_name=="Stress.protocol" else \
            1 if simple_name=="Region" else \
            2 if simple_name=="Time_from_stress.h" else \
            3
    
    files.sort(key=lambda x: ordering[x])
    
    for file in files:
        simple_name = os.path.basename(file)
        image = create_new_image("imgs/phenotypic_information/"+simple_name, width="70%")
        add_element_to_multi_element(result, image)
    
    return HttpResponse(json.dumps(result))

def search_by_gene_symbol(request):
    print(str(datetime.datetime.now()))

    data = json.loads(request.body.decode('utf-8'))
#     data = {}
    print(data)
    
    bioproject = data["bioproject"]
    gene_symbol = data["gene_name_sy"]
#     gene_symbol = "DUSP6"
    
    offset = 0
    limit = 10
    
    if "offset" in data: offset = data["offset"]
    if "limit" in data: limit = data["limit"]
    
    rows = []

    with lock:
        basedir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(basedir + "bg.RData")
        SearchByGene = robjects.r("SearchByGene")
        results = SearchByGene(gene_symbol, bg)
    
    # Make the call
    print(results, len(results), results.names, results[0])
    
    total = len(results)
    
    header = []
    for colname in ["Sample ID", "FPKM value"]:
        header.append({
            "label": colname,
            "title": colname,
            "tooltip": colname,
            "filters": {
                "title": colname + " filters:",
                "list": [
                    {
                        "type": "select",
                        "key": colname,
                        "title": "Select a "+colname+":",
                        "placeholder": "",
                        "operators": "LIKE",
                        "chosen_value": ""
                    }
                ]
            }
        })
    
    for i in range(total):
        row_dict = {}
        
        sample_id = results.names[i].replace("FPKM.", "")
        sample_id = results.names[i].replace("trimmed_", "")
        value = results[i]
        
        row_dict["Sample ID"] = [{
            "type": "text",
            "label": str(sample_id),
            "color": "black"
        }]
        
        row_dict["FPKM value"] = [{
            "type": "text",
            "label": str(value),
            "color": "black"
        }]
        
        rows.append(row_dict)
    
    response = {"structure": {"field_list": header}, "total": total, "hits": rows}
    
    return HttpResponse(json.dumps(response))

def see_gene_isoforms(request):
    print(str(datetime.datetime.now()))

    data = json.loads(request.body.decode('utf-8'))
#     data = {}
    print(data)
    
    bioproject = data["bioproject"]
    gene_symbol = data["gene_name_sy"]
#     gene_symbol = "DUSP6"
    
    offset = 0
    limit = 10
    
    if "offset" in data: offset = data["offset"]
    if "limit" in data: limit = data["limit"]
    
    rows = []

    with lock:
        dir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(dir + "bg.RData")
        results = robjects.r("SearchGeneIsoforms")(gene_symbol, bg)
        if results is rpy2.rinterface.NULL: return HttpResponse(json.dumps(empty_table()))
        
    response = to_table(results, offset, limit)

    return HttpResponse(json.dumps(response))

def search_by_transcript_symbol(request):
    print(str(datetime.datetime.now()))

    data = json.loads(request.body.decode('utf-8'))
    print(data)
    
    bioproject = data["bioproject"]
    transcript_symbol = data["transcript_name_sy"]
    
    offset = 0
    limit = 10
    
    if "offset" in data: offset = data["offset"]
    if "limit" in data: limit = data["limit"]
    
    with lock:
        dir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(dir + "bg.RData")
        SearchByTranscript = robjects.r("SearchByTranscript")
        results = SearchByTranscript(transcript_symbol, bg)
    
    response = to_table(results, offset, limit)
    
    return HttpResponse(json.dumps(response))

def search_by_feature(request):
    print(str(datetime.datetime.now()))

    data = json.loads(request.body.decode('utf-8'))
    print(data)
    
    bioproject = data["bioproject"]
    gene_symbol = data["gene_name_sy"]
    feature = data["feature"]
    
    offset = 0
    limit = 10
    
    if "offset" in data: offset = data["offset"]
    if "limit" in data: limit = data["limit"]
    
    with lock:
        dir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(dir + "bg.RData")
        search = robjects.r("SearchByFeature")
        results = search(gene_symbol, feature, bg)
    
    response = to_table(results, offset, limit)
    
    return HttpResponse(json.dumps(response))

def search_by_condition(request):
    
    data = json.loads(request.body.decode('utf-8'))
    print(data)
    
    conditions = []
    for x in range(1, 6):
        conditionId = "condition"+str(x)
        conditionValueId = "condition_value"+str(x)
        
        if conditionId in data:
            condition = data[conditionId]
            if condition == "ALL": continue
            
            condition_value = data[conditionValueId]    
            conditions.append(condition + "=='" + str(condition_value)+ "'")
    final_conditions = " & ".join(conditions)
    
    bioproject = data["bioproject"]
    gene = data["gene_name_sy"]
    
    offset = 0
    limit = 10
    
    if "offset" in data: offset = data["offset"]
    if "limit" in data: limit = data["limit"]
    
    print("QUERY", final_conditions, gene)
    
    with lock:
        dir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(dir + "bg.RData")
        results = robjects.r("SearchByCondition")(final_conditions, gene, bg)
        if results is rpy2.rinterface.NULL: return HttpResponse(json.dumps(empty_table()))
    
    response = to_table(results, offset, limit)
    
#     preferential_order = ["chr", "start", "end", "strand", "gene"]
#     header = response["structure"]["field_list"]
#     rows = response["hits"]
#     header.sort(key=lambda x: preferential_order.index(x["label"]) if x["label"] in preferential_order else sys.maxsize)
    
    return HttpResponse(json.dumps(response))

def gene2id():
    
    map = {}
    
    # Download file from here: "ftp://ftp.ncbi.nlm.nih.gov/genomes/refseq/vertebrate_mammalian/Mus_musculus/reference/GCF_000001635.26_GRCm38.p6/GCF_000001635.26_GRCm38.p6_genomic.gff.gz"
    # and extracted two-column file with the following command
    # zcat GCF_000001635.26_GRCm38.p6_genomic.gff.gz | cut -f 9 | grep "Name=" | tr ';' '\t' | grep "GeneID" | grep "ID=gene" | cut -f 2,3 | sed 's/Dbxref=GeneID://g' | sed 's/Name=//g' | sed 's/,[^\t]*//g' | awk '{ print $2"\t"$1}'
    # TODO: make it perfect by considering this border-case:
    # NC_000068.7     BestRefSeq      gene    175470025       175480553       .       +       .       ID=gene6037;Dbxref=GeneID:100503949,MGI:MGI:3779822;Name=Zfp965;description=zinc finger protein 965;gbkey=Gene;gene=Zfp965;gene_biotype=protein_coding;gene_synonym=668009,Gm8923
    # in which DESeq uses a synonym for the name of the gene (e.g.. Gm8923 or Gm10094)
    with open(os.path.dirname(__file__) + "/utils/genename2id.tsv") as reader:
        for line in reader:
            gene_name, gene_id = line.strip().split("\t")
            map[gene_name] = {"id": gene_id}
    
    with open(os.path.dirname(__file__) + "/utils/Mus_musculus.GRCm38.93.genes.gtf") as reader:
        for line in reader:
            fields = line.strip().split("\t")
            chr, start, end, strand, info = [fields[i] for i in [0,3,4,6,8]]
            gene_name = None
            
            for f in info.split(";"):
                if "gene_name" in f:
                    gene_name = f.strip().split(" ")[1].replace("\"", "")
            
            if gene_name is not None:
                
                if gene_name not in map:
                    map[gene_name] = {"id": "UNKNOWN"}
                
                gene_info = map[gene_name]
                gene_info["chr"] = "chr" + chr
                gene_info["start"] = start
                gene_info["end"] = end
                gene_info["strand"] = strand
            
    return map
            

def search_by_diff_fold_expr(request):

    data = json.loads(request.body.decode('utf-8'))
    print(data)
    
#     feature = data["feature"]
#     covariate = data["covariate"]
    
#     conditions = []
#     for x in range(1, 6):
#         conditionId = "condition"+str(x)
#         conditionValueId = "condition_value"+str(x)
#         
#         if conditionId in data:
#             condition = data[conditionId]
#             if condition == "ALL": continue
#             
#             condition_value = data[conditionValueId]    
#             conditions.append(condition + "=='" + str(condition_value)+ "'")
#     final_conditions = " & ".join(conditions)
    
    bioproject = data["bioproject"]
#     covariance = float(data["covariance"]) if data["covariance"] != "ALL" else 1
    pvalue = float(data["pvalue"]) if data["pvalue"] != "ALL" else sys.maxsize
    qvalue = float(data["qvalue"]) if data["qvalue"] != "ALL" else sys.maxsize
    min_fold_change = float(data["min_fold_change"]) if data["min_fold_change"] != "ALL" else sys.maxsize
    
    offset = 0
    limit = 10
    
    if "offset" in data: offset = data["offset"]
    if "limit" in data: limit = data["limit"]
    
    gene2idmap = gene2id()
    
    total = 0
    n = -1
    header = []
    rows = []
    with open(os.path.dirname(__file__) + "/data/degs/"+bioproject+"/sorted.DEG.csv") as reader:
        for line in reader:
            line = line.strip()
            
            n += 1
            if n == 0:
                header = line.split(" ")
                
                header = [header[0]] + ["Genomic position", "strand"] + header[1:] #+ ["Link to NCBI"]
                
                header = [{
                    "label": colname,
                    "title": colname,
                    "tooltip": colname,
                    "filters": {
                        "title": colname + " filters:",
                        "list": [
                            {
                                "type": "select",
                                "key": colname,
                                "title": "Select a "+colname+":",
                                "placeholder": "",
                                "operators": "LIKE",
                                "chosen_value": ""
                            }
                        ]
                    }
                } for colname in header]
                
                continue
            
            gene, mean, gene_logfc, gene_lfcSE, gene_stat, gene_pvalue, gene_qvalue = fields = line.split(" ")
            if gene_logfc == "NA" or float(gene_logfc) < min_fold_change: continue
            if gene_pvalue == "NA" or float(gene_pvalue) > pvalue: continue
            if gene_qvalue == "NA" or float(gene_qvalue) > qvalue: continue
            
            total += 1
            
            if total <= offset: continue
            if total > offset + limit: continue
            
            gene_name = fields[0]
            gene_info = gene2idmap[gene_name]
            row = {}
            for (i, h) in enumerate(header):
                
                if i == 0:
                    value = fields[0]
                elif i==1:
                    value = gene_info["chr"] + ":" + gene_info["start"] + "-" + gene_info["end"]
                elif i==2:
                    value = gene_info["strand"]
                elif h["label"] == "pvalue" or h["label"] == "padj":
                    value = '%.2E' % Decimal(float(fields[i-2]))
                else:
                    value = "{0:.2f}".format(round(float(fields[i-2]), 2))
                
                if i == 0 and "id" in gene_info:
                    gene_id = gene_info["id"]
                    obj = create_new_link("https://www.ncbi.nlm.nih.gov/gene/" + gene_id, value, "See "+value+" in NCBI")
                elif i == 1:
                    obj = create_new_link("http://genome.ucsc.edu/cgi-bin/hgTracks?db=mm10&pix=800&position=" + value, value, "See on Genome browser")
                else: obj = {
                        "type": "text",
                        "label": value,
                        "color": "black"
                    }
                
                row[h["label"]] = []
                if i==0:
                    row[h["label"]].append(create_new_image("imgs/gene-icon.png", width="35px"))
                row[h["label"]].append(obj)
            
            
#             row["Link to NCBI"] = []
            
#             if gene_name in gene2idmap:
# #                 gene_info = gene2idmap[gene_name]
#                 gene_id = gene_info["id"]
#                 row["Link to NCBI"].append(create_linkable_image("imgs/gene-icon.png", "https://www.ncbi.nlm.nih.gov/gene/" + gene_id, tooltip="See the "+gene_name+" gene in NCBI", width="35px"))
            
            rows.append(row)
            
    
#     print("QUERY", final_conditions, covariate, feature)
#     with lock:
#         dir = BASE_DATA_DIR + bioproject + "/"
#         bg = get_ballgown_object(dir + "bg.RData")
#         results = robjects.r("SearchByDiffFoldExpr")(final_conditions, covariate, feature, bg)
#         if results is rpy2.rinterface.NULL: return HttpResponse(json.dumps(empty_table()))
#         
#         results = robjects.r("StatsFiltering")(results, qvalue, pvalue, min_fold_change)
#         if results is rpy2.rinterface.NULL: return HttpResponse(json.dumps(empty_table()))
    
#     response = to_table(results, offset, limit)
    
    
    response = {"structure": {"field_list": header}, "total": total, "hits": rows}
    
#     preferential_order = ["chr", "start", "end", "strand", "gene_id", "gene_name"]
#     header = response["structure"]["field_list"]
#     header.sort(key=lambda x: preferential_order.index(x["label"]) if x["label"] in preferential_order else sys.maxsize)
    
    return HttpResponse(json.dumps(response))

def gene_plotter(request):
    print(str(datetime.datetime.now()))

    data = json.loads(request.body.decode('utf-8'))
    print(data)
    
    bioproject = data["bioproject"]
    gene_symbol = data["gene_name_sy"]
    measure = data["measure"]
    covariate = data["covariate"]

#     gene_symbol = "DUSP11"
#     measure = "FPKM"
#     covariate = "time_h"
    
    offset = 0
    limit = 10
    
    if "offset" in data: offset = data["offset"]
    if "limit" in data: limit = data["limit"]

    basedir = os.path.dirname(__file__) + "/../../material/imgs/temp/"
    if not os.path.exists(basedir):
        os.makedirs(basedir)
        
    with lock:
        dir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(dir + "bg.RData")
        results = robjects.r("Gene_Plotter_By_Group")(gene_symbol, measure, covariate, basedir, bg)
        if results is rpy2.rinterface.NULL: return HttpResponse(json.dumps(empty_table()))
    
    print(results)
    print(type(results))
    print(results.names)
#     print(results[results.names[0]])
#     print(results[results.names[1]])
#     print(results[results.names[2]])
#     print(results[results.names[3]])
#     print(type(results[0]))
#     print(results[0])
#     print(results[1])
#     print(results[2])
#     print(results[3])
    
    transcripts = results[0]
    chromosomes = results[1]
    starts = results[2]
    ends = results[3]
    
    print("CHROMOSOMES", chromosomes)
    print("STARTS", starts)
    print("ENDS", ends)
    chromosome = chromosomes[0]
    min_start = min(starts)
    max_end = max(ends)
    print(chromosome, min_start, max_end)
    
    filename = results[4][0]
    if os.path.exists(filename):
        os.rename(filename, basedir + filename)
        
        response = create_new_image("imgs/temp/" + filename, "100%")
        
        return HttpResponse(json.dumps(response))
    else:
        return HttpResponse(json.dumps(create_error_message(filename)))
    
def empty_table():
    return {"structure": {"field_list": []}, "total": 0, "hits": []}

def to_table(results, offset, limit):
    total = results.nrow
    
    rows = []
    header = []
    n = results.ncol
    
    i = -1
    for result in results.iter_row():
        i += 1
        if i < offset: continue
        if len(rows) >= limit: break
        
        row_dict = {}
        
        colnames = result.colnames
        
        for i in range(0, n):
            item = result[i]
            colname = colnames[i]
            colname = simplify_column(colname)
            
            if hasattr(item, 'levels'):
                value = str(item.levels[item[0]-1])
            else:
                value = item[0]
            
            if value is rpy2.rinterface.NA_Character:
                value = "N/A"
            
            row_dict[colname] = [{
                "type": "text",
                "label": value,
                "color": "black"
            }]
        
        rows.append(row_dict)
    
    header = []
    for colname in results.colnames:
        colname = colname
        colname = simplify_column(colname)
        
        header.append({
            "label": colname,
            "title": colname,
            "tooltip": colname,
            "filters": {
                "title": colname + " filters:",
                "list": [
                    {
                        "type": "select",
                        "key": colname,
                        "title": "Select a "+colname+":",
                        "placeholder": "",
                        "operators": "LIKE",
                        "chosen_value": ""
                    }
                ]
            }
        })
        
    response = {"structure": {"field_list": header}, "total": total, "hits": rows}
    
    return response

def simplify_column(column):
    return column.replace("trimmed_", "")

def get_ballgown_object(path):
    
    bg = cache.get(path)
    if bg is None:
        print("OBJECT 'BG' NOT FOUND IN CACHE", path)
        base = init()
        base.load(path)
        bg = robjects.r("bg")
        print("ADDING OBJECT 'BG' INTO CACHE", path)
        cache.set(path, bg, None)
    else:
        print("OBJECT 'BG' FOUND IN CACHE", path)
        
    return bg

def create_entry(id, label, img=None):
    entry = {"id": id, "label": label}
    if img is not None:
        entry["img"] = img
        
    return entry

def get_projects(request):
    results = []
    
    map = load_dataset_info()
#     for dir in glob.glob(os.path.dirname(__file__) + "/data/*"):
#         if os.path.isdir(dir):

    for bioproject_id in sorted(map.keys(), key=lambda x: int(x.split(".")[0]) if "." in x else int(x.split("PRJNA")[1])):
#             name = os.path.basename(dir)
        results.append(create_entry(bioproject_id, bioproject_id, "imgs/project.png"))
    
    return HttpResponse(json.dumps(results))

def simple_genes(request):
    print("SIMPLE GENES")
    return HttpResponse(json.dumps("SIMPLE GENES"))

def genes(request, bioproject, prefix = ""):
    print("GENES WITH PREFIX", bioproject, prefix)
    
    with lock:
        basedir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(basedir + "bg.RData")
        getGenes = robjects.r("getGenes")
        all_genes = getGenes(bg)
    
    response = []
    
    genes = set()
    for gene_id in all_genes:
        id = str(gene_id)
        if prefix not in id: continue
        if len(genes) >= 50: break
        
        genes.add(id)
    
    for gene in sorted(genes):
        response.append({"id": gene, "label": gene, "img": "imgs/gene-icon.png"})
        
    if len(response) > 1:
        response.insert(0, {"id": "ALL", "label": "Include any gene", "img": "imgs/gene-icon.png"})
    
    return HttpResponse(json.dumps(response))

def features(request):
    
    response = []
    
    response.insert(0, {"id": "ALL", "label": "Include any feature", "img": "imgs/transcript-icon.png"})
    for feature in ["Exon", "Intron", "Trans"]:
        response.append({"id": feature.lower(), "label": feature, "img": "imgs/transcript-icon.png"})
    
    return HttpResponse(json.dumps(response))

def transcripts(request, bioproject, prefix = ""):
    
    with lock:
        basedir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(basedir + "bg.RData")
        fx = robjects.r("getTranscript")
        all_transcripts = fx(bg)
    
    response = []
    
    response.insert(0, {"id": "ALL", "label": "Include any transcript", "img": "imgs/gene-icon.png"})
    transcripts = set()
    for transcript_id in all_transcripts:
        id = str(transcript_id)
        if prefix not in id: continue
        if len(transcripts) >= 50: break
        
        transcripts.add(id)
    
    for transcript in sorted(transcripts):
        response.append({"id": transcript, "label": transcript, "img": "imgs/gene-icon.png"})
    
    return HttpResponse(json.dumps(response))

def covariates(request, bioproject):
    
    with lock:
        basedir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(basedir + "bg.RData")
        fx = robjects.r("getCovariates")
        phenodata = fx(bg)
    
    response = []
    
    response.insert(0, {"id": "ALL", "label": "Include any covariate", "img": "imgs/covariate.png"})
    covariates = set()
    for col_name in phenodata.colnames:
        if col_name == "ids": continue
        covariates.add(col_name)
    
    for covariate in covariates:
        response.append({"id": covariate, "label": covariate, "img": "imgs/covariate.png"})
    
    return HttpResponse(json.dumps(response))

def measures(request):
    
    response = []
    
    response.insert(0, {"id": "ALL", "label": "Include any measure", "img": "imgs/measure.png"})
    for measure in ["FPKM", "Cov"]:
        response.append({"id": measure, "label": measure, "img": "imgs/measure.png"})
    
    return HttpResponse(json.dumps(response))

def covariate_values(request, bioproject, covariate):
    
    with lock:
        basedir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(basedir + "bg.RData")
        fx = robjects.r("getCovariates")
        phenodata = fx(bg)
    
    covariates = {}
    for colname in phenodata.colnames:
        index = phenodata.colnames.index(colname)
        
        values = set()
        for result in phenodata.iter_row():
            x = result[index]
            
            if hasattr(x, 'levels'):
                value = str(x.levels[x[0]-1])
            else:
                value = x[0]
    
            values.add(value)
        
        response = []
        
        for value in values:
            response.append({"id": value, "label": value, "img": "imgs/covariate.png"})
            
        covariates[colname] = response
    
    index = phenodata.colnames.index(covariate)
    if index < 0:
        return HttpResponse(json.dumps("No such covariate ({}) in data.".format(covariate)))
    
    values = set()
    for result in phenodata.iter_row():
        x = result[index]
        
        if hasattr(x, 'levels'):
            value = str(x.levels[x[0]-1])
        else:
            value = x[0]

        values.add(value)
    
    response = []
    
    for value in values:
        response.append({"id": value, "label": value, "img": "imgs/covariate.png"})
    
    return HttpResponse(json.dumps(response))

def downloads(request):
    return HttpResponse(json.dumps(empty_table()))


def bioproject(request, bioproject_id):
    
    map = load_dataset_info()
    bioproject_info = map[bioproject_id]
    
    multielement = create_new_multi_element(layout="column", alignment="start start")
    add_element_to_multi_element(multielement, create_new_paragraph("<b>Bioproject ID</b>: " + bioproject_id))
    add_element_to_multi_element(multielement, create_new_paragraph("<b>Size (GB)</b>: " + convert_bytes(bioproject_info["size"])))
    add_element_to_multi_element(multielement, create_new_paragraph("<b>Organism</b>: " + bioproject_info["organism"]))
    add_element_to_multi_element(multielement, create_new_paragraph("<b>Platform(s)</b>: " + ", ".join(bioproject_info["platform"])))
#     add_element_to_multi_element(multielement, create_new_paragraph("<b>Experiments</b>: " + str(bioproject_info["experiments"])))
#     add_element_to_multi_element(multielement, create_new_paragraph("<b>Samples</b>: " + str(bioproject_info["samples"])))
    
    return HttpResponse(json.dumps(multielement))

def papers(request, bioproject_id):
    
    map = load_dataset_info()
    bioproject_info = map[bioproject_id]
    header = ["Paper link", "Filename", "Abstract"]
    rows = []
    for paper in bioproject_info["paper_id"]:
        paper_row = []
        paper_row.append(create_linkable_image("imgs/paper.png", paper["url"], width="50px", tooltip="Click to read the paper"))
        paper_row.append(create_new_text(paper["url"].split("/")[-1] if paper["source"] == "manual" else "Paper Pubmed ID:" + paper["id"]))
        paper_row.append("coming soon")
#         paper_row = create_row(paper_table)
#         paper_row["Paper link"] = create_linkable_image("imgs/paper.png", paper["url"], width="100px")
#         paper_row["Abstract"] = "Abstract of paper " + str(paper["id"])
        rows.append(paper_row)
        
#         add_row(paper_table, paper_row)
    return HttpResponse(json.dumps({"type": "table", "subdata": {"total": len(rows), "header": header, "items": rows}}))

def data_info(request, bioproject_id):
    map = load_dataset_info()
    bioproject_info = map[bioproject_id]
    return HttpResponse(json.dumps(create_chart("chart-bar", width="400px", xaxis="Dimensions", data=[("Number of experiments", bioproject_info["experiments"]), ("Number of samples", bioproject_info["samples"])])))

def phenodata_info(request, bioproject_id):
#     map = load_dataset_info()
#     bioproject_info = map[bioproject_id]
    
    filepath = os.path.dirname(__file__) + "/data/phenodata/"+ bioproject_id + "/phenodata.csv"
    line_no = 0
    header = []
    counters =  {}
    with open(filepath, "r") as reader:
        for line in reader:
            line = line.strip()
            
            line_no += 1
            
            fields = line.split(",")
            
            if line_no == 1:
                header = fields
                for h in header[1:]:
                    counters[h] = Counter()
            else:
                for i in range(len(fields)):
                    if i==0: continue
                    
                    key, value = [header[i], fields[i]]
                    counters[key][value] += 1
    
    multielement = create_new_multi_element(layout="row", alignment="start start")
    for key,counter in counters.items():
        if key in ["Replicate"]: continue
        
        data = []
        for v in counter:
            data.append((v, counter[v]))
        
        if len(data) == 1 and counter.most_common()[0][0] in ["na", "NA", "N/A"]: continue
        
        chart = create_chart("chart-bar", min=0, descriptions=[key, "Quantity"], width="400px", data=data)
        chart["style"] = {
            'padding-bottom': '75px'
        }
        add_element_to_multi_element(multielement, chart)        
        
    return HttpResponse(json.dumps(multielement))

from stress_mice.utils import selector
def get_criteria(request):
    data = json.loads(request.body.decode('utf-8'))
    print(data)
    bioproject = data["bioproject"]
    del data["bioproject"]
    
    # Build old choices
    response = []
    for (key,value) in data.items():
        select = create_select([{"id": value, "label": str(value)}], label=key, value={"id": value, "label": str(value)}, key=key)
        select["data"]["onChange"] = [{
            "key": key,
            "action":"write",
            "scope": "global"
        },{
            "action": "write",
            "scope": "global",
            "key": "update",
            "value": "true"
        }]
        response.append(select)
    response.sort(key=lambda x: x["key"])
    
    # Build new choices (if any!)
    user_filter = None
    user_filter_clauses = []
    user_filter_keys = set()
    for (key,value) in data.items():
        user_filter_clauses.append(value)
        (k, v) = value.split("==")
        user_filter_keys.add(k)
    print("ALREADY USED", user_filter_keys)
    
    if user_filter_clauses:
        user_filter = "(" + " & ".join(["("+str(x)+")" for x in user_filter_clauses]) + ")"
    print("FILTER", user_filter_clauses, user_filter)
    
    new_choices = set()
    counts = Counter()
    conditions = selector.select(os.path.dirname(__file__) + "/data/configurations.tsv", user_filter, bioproject, only_leaves=False, output_other_clauses_only=True)
    for condition in conditions:
        for clause in condition:
            counts[clause] += 1
            (k, v) = clause.split("==")
            if v.replace("\"", "").startswith("control"): continue
            
            if k not in user_filter_keys:
                new_choices.add(clause)

    print("CONDITIONS", len(conditions))
    print("COUNTS", counts)
    for c in counts:
        if counts[c] == len(conditions) and c in new_choices:
            new_choices.remove(c)
                
    new_choices = sorted(new_choices)
    
    if len(conditions) > 1 and len(new_choices) > 0:
        new_key = "Criterion"+str(len(response)+1)
        select = create_select([{"id": x, "label": x} for x in new_choices], label=new_key, key=new_key)
        select["data"]["onChange"] = [{
                "key": new_key,
                "action":"write",
                "scope": "global"
            },{
            "action": "write",
            "scope": "global",
            "key": "update",
            "value": "true"
        }]
        response.append(select)
    
    print("RESPONSE", response)
        
    return HttpResponse(json.dumps(response))







