import pandas as pd

ETHNICITY_MAP = {
    "Arab": "Arab",
    "Asian - Bangladeshi": "Asian",
    "Asian - Chinese": "Chinese",
    "Asian - Indian": "Indian",
    "Asian - Other": "Asian",
    "Asian - Pakistani": "Asian",
    "Asian or Asian British - Bangladeshi": "Asian",
    "Asian or Asian British - Indian": "Indian",
    "Asian or Asian British - Pakistani": "Asian",
    "Black - African": "Black",
    "Black - Caribbean": "Black",
    "Black - Other": "Black",
    "Black or Black British - African": "Black",
    "Black or Black British - Caribbean": "Black",
    "Chinese": "Chinese",
    "Gypsy or Traveller": "Other/Unknown",
    "Mixed - Other": "Other/Unknown",
    "Mixed - White and Asian": "Asian",
    "Mixed - White and Black African": "Black",
    "Mixed - White and Black Caribbean": "Black",
    "Not known": "Other/Unknown",
    "Other": "Other/Unknown",
    "Other/Unknown": "Other/Unknown",
    "Other Asian background": "Asian",
    "Other Black background": "Black",
    "Other Mixed background": "Other/Unknown",
    "Other White background": "White",
    "Other ethnic background": "Other/Unknown",
    "Prefer not to say": "Other/Unknown",
    "Unknown": "Other/Unknown",
    "White": "White",
    "White - British": "White",
    "NaN": "Other/Unknown",
}


def applicants_to_bar(applicants, primary_type, secondary_type=None, combined=False):
    df = pd.DataFrame(applicants)
    reformatted = []

    if primary_type == "ethnicity":
        df["ethnicity"] = df["ethnicity"].map(ETHNICITY_MAP)

    if secondary_type is not None:
        counted = df[[primary_type, secondary_type]].value_counts()
        for key, value in counted.items():
            if combined:
                existing_combined = list(
                    filter(
                        lambda x: x[primary_type] == "Combined" and x["type"] == key[1],
                        reformatted,
                    )
                )
                if len(existing_combined) > 0:
                    reformatted.remove(existing_combined[0])
                    reformatted.append(
                        {
                            primary_type: "Combined",
                            "count": int(value) + existing_combined[0]["count"],
                            "type": key[1],
                        }
                    )
                else:
                    reformatted.append(
                        {
                            primary_type: "Combined",
                            "count": int(value),
                            "type": key[1],
                        }
                    )
            reformatted.append(
                {
                    primary_type: key[0],
                    "count": int(value),
                    "type": key[1],
                }
            )
        reformatted = list(sorted(reformatted, key=lambda x: -x["count"]))
        return reformatted

    counted = df[primary_type].value_counts()
    for key, value in counted.items():
        if key.strip() != "":
            if combined:
                reformatted.append(
                    {primary_type: "Combined", "count": int(value), "type": key}
                )
            reformatted.append({primary_type: key, "count": int(value), "type": key})
    return reformatted


def applicants_to_pie(applicants, primary_type, top=0):
    df = pd.DataFrame(applicants)

    if primary_type == "ethnicity":
        df["ethnicity"] = df["ethnicity"].map(ETHNICITY_MAP)

    reformatted = []
    counted = df[primary_type].value_counts()
    for key, value in counted.items():
        reformatted.append({"type": key, "value": int(value)})

    reformatted = list(sorted(reformatted, key=lambda x: -x["value"]))
    if top > 0 and top < len(reformatted):
        topN = reformatted[:top]
        others = {"type": "Others", "value": 0}
        for i in reformatted[top:]:
            others["value"] += i["value"]
        topN.append(others)
        return topN

    return reformatted
