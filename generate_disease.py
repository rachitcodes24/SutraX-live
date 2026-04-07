import json
import random

# Real base diseases with accurate causes and treatments
base_diseases = [
    {
        "base_name": "Diabetes Mellitus",
        "cause": "Insulin resistance or failure of the pancreas to produce sufficient insulin. Strongly linked to genetic factors and lifestyle choices.",
        "treatment": "Metformin, Sulfonylureas, Insulin therapy, and strict dietary monitoring."
    },
    {
        "base_name": "Coronary Artery Disease",
        "cause": "Atherosclerosis (plaque buildup) in coronary arteries, often driven by hypertension, high LDL cholesterol, and smoking.",
        "treatment": "Statins, Beta-blockers, ACE inhibitors. Surgical interventions like Angioplasty or CABG."
    },
    {
        "base_name": "Asthma",
        "cause": "Chronic inflammation of the airways triggered by environmental allergens, cold air, or genetic susceptibility.",
        "treatment": "Inhaled corticosteroids, Albuterol (short-acting beta-agonists), Leukotriene modifiers."
    },
    {
        "base_name": "Chronic Kidney Disease",
        "cause": "Prolonged renal damage typically resulting from uncontrolled diabetes and long-standing hypertension.",
        "treatment": "ACE inhibitors for blood pressure management, protein-restricted diet. Dialysis or transplant in end-stage cases."
    },
    {
        "base_name": "Rheumatoid Arthritis",
        "cause": "Autoimmune condition where the immune system attacks the synovium lining the joints, causing chronic inflammation.",
        "treatment": "DMARDs (e.g., Methotrexate), NSAIDs, and TNF inhibitors."
    },
    {
        "base_name": "Alzheimer's Disease",
        "cause": "Neurodegenerative disorder characterized by amyloid-beta plaques and tau tangles leading to progressive brain cell death.",
        "treatment": "Cholinesterase inhibitors (Donepezil), NMDA receptor antagonists. Focus is on symptom management."
    },
    {
        "base_name": "Major Depressive Disorder",
        "cause": "Complex interplay of neurotransmitter imbalances (serotonin/dopamine), genetic predisposition, and environmental stress.",
        "treatment": "SSRIs, SNRIs, combined with Cognitive Behavioral Therapy (CBT)."
    },
    {
        "base_name": "Hypertension",
        "cause": "Chronic elevation of blood pressure often linked to genetic factors, obesity, high sodium intake, and stress.",
        "treatment": "Thiazide diuretics, Calcium channel blockers, ACE inhibitors/ARBs, and DASH diet."
    },
    {
        "base_name": "Chronic Obstructive Pulmonary Disease",
        "cause": "Long-term exposure to particulate matter or irritating gases, predominantly from chronic tobacco smoking.",
        "treatment": "Bronchodilators (LABA/LAMA), inhaled corticosteroids, pulmonary rehabilitation, smoking cessation."
    },
    {
        "base_name": "Migraine",
        "cause": "Neurological condition involving altered nerve pathways and neurochemical imbalances. Triggered by stress or hormonal shifts.",
        "treatment": "Triptans, NSAIDs for acute attacks. Beta-blockers or Topiramate for prevention."
    }
    # (The script will automatically multiply these into 1000+ variants)
]

variants = [
    "Acute", "Chronic", "Stage I", "Stage II", "Stage III", "Severe", 
    "Mild", "Pediatric", "Geriatric", "Type A", "Type B", "Drug-Resistant"
]

sources = ["FedHealth DB", "WHO API Sync", "CDC OpenData", "National EHR Registry", "Mayo Clinic Data Pool"]
hospitals = ["A", "B", "C", "D", "E", "F"]

generated_database = []
disease_id_counter = 1

print("Generating 1000+ federated disease records...")

# Generate exactly 1,200 records by combining base diseases with variants and localized data
for i in range(120):  # loop 120 times
    for base in base_diseases:
        
        # Pick a random variant (e.g. "Acute Asthma", "Stage II Chronic Kidney Disease")
        variant = random.choice(variants)
        full_name = f"{variant} {base['base_name']} (Variant {random.randint(100,999)})"
        
        # Randomize patient counts to look like real hospital data
        patient_count = random.randint(50, 85000)
        
        # Randomize which hospital nodes contributed this data
        num_nodes = random.randint(1, 4)
        node_list = random.sample(hospitals, num_nodes)
        node_string = "Hospitals " + ", ".join(node_list)

        record = {
            "id": disease_id_counter,
            "name": full_name,
            "source": random.choice(sources),
            "cause": base["cause"],
            "treatment": base["treatment"],
            "patientCount": patient_count,
            "nodes": node_string
        }
        generated_database.append(record)
        disease_id_counter += 1

# Save the 1200 records to diseases.json
with open('diseases.json', 'w') as f:
    json.dump(generated_database, f, indent=4)

print(f"Successfully generated {len(generated_database)} records and saved to 'diseases.json'.")