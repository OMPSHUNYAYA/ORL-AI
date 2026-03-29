# ⭐ **ORL-AI — Test Guide**

**Orderless Intelligence — Structural Decision System**

**Deterministic • Order-Free • Time-Independent Decision Resolution**

**Powered by Shunyaya Framework (STOCRS + SSUM-Time + ORL)**

---

## ⚡ **Start Here — Run the Demo (Recommended)**

Open terminal in the project root (Command Prompt / PowerShell / Terminal).

Run:

```
python demo/orl_ai_demo_base_v4_1.py
```

That’s it.

---

## 🧪 **Generate Verifiable Output (Recommended)**

Run:

```
python demo/orl_ai_demo_base_v4_1.py --write-output --output outputs/orl_ai_result_v4_1.json
```

This produces:

• deterministic structural decisions  
• governance-aware resolution output  
• reproducible JSON for verification  

---

## 👀 **What You Will See**

• Multiple independent nodes (A, B, C, etc.)  
• Each node starts with partial signals  
• No timestamps anywhere  
• No ordering assumptions  
• No synchronization between nodes  

Then:

• Structures are merged  
• Rules are evaluated  
• Conflicts are detected and contained  
• Ambiguity is rejected  
• Valid decisions are accepted  
• All nodes converge to the same result  

---

## 🧭 **What This Demo Is Showing**

ORL-AI is **not a traditional AI system**.

Instead of:

• training-based inference  
• order-dependent processing  
• probabilistic outputs  

It:

• evaluates structural completeness  
• enforces consistency  
• resolves decisions only when uniquely valid  
• guarantees deterministic convergence  

---

## 🔬 **Demo Scenarios**

### **1. Reference Scenario (3-node convergence)**

**Input:**

Node A → {fever}  
Node B → {cough}  
Node C → {fatigue}  

**Result:**

• initial → **INCOMPLETE**  
• merged → **RESOLVED → Action_Isolate**

---

### **2. Replay Scenario (Order Independence)**

Different grouping:

{cough, fatigue} + {fever}

**Result:**

• same final structure  
• same decision  
• same certificate  

---

### **3. Conflict Scenario**

**Input includes:**

{fatigue, no_fatigue}

**Result:**

• **ABSTAIN**  
• decision rejected  
• conflict explicitly detected  

---

### **4. Ambiguity Scenario**

Multiple incompatible decisions are supported by the structure.

**Result:**

• **ABSTAIN**  
• ambiguity detected  
• no unsafe resolution  

---

### **5. Multi-Node Convergence (5-node)**

Distributed partial inputs.

**Result:**

• **RESOLVED**  
• deterministic convergence across nodes  

---

### **6. Domain Portability**

Different domains:

• Approve path  
• Escalate path  

**Result:**

• same structural law  
• different valid decisions  

---

## ⚖️ **Decision States**

**RESOLVED**

• structure is sufficient  
• no conflict  
• exactly one decision is supported  

---

**INCOMPLETE**

• missing required inputs  
• no forced decision  

---

**ABSTAIN**

• conflicting inputs OR  
• multiple incompatible decisions  

---

## 📊 **What to Observe Carefully**

### **No Time Anywhere**

• no timestamps  
• no clocks  

### **No Order Dependency**

• input order does not matter  

### **Different Start States**

Node A ≠ Node B initially  

### **Same Final Decision**

After merge:

Node A == Node B  

---

## 🔍 **Structural Guarantees**

same normalized structure → same decision
same normalized structure → same certificate

missing structure → **INCOMPLETE**  
conflicting structure → **ABSTAIN**  
ambiguous structure → **ABSTAIN**  

resolution is a deterministic function of `normalize(structure)`

---

## 🔐 **Acceptance Law (Formal)**

A decision is accepted only when:

`normalize(structure)` satisfies:

- sufficient_structure  
- conflict_free  
- uniquely_valid  

---

## 🔁 **Deterministic Behavior**

Run the demo multiple times.

You will observe:

• identical decisions  
• identical governance outcomes  
• identical certificates  

---

## 🔁 **Replay Guarantee**

Given the same structure:

`resolve(normalize(structure)) -> identical decision`

This ensures:

• reproducibility  
• auditability  
• cross-system verification  

---

## 📌 **Core Insight**

ORL-AI does **not require**:

• time  
• order  
• synchronization  

It requires only:

**structure**

---

## 📐 **Core Identity**

`decision = resolve(normalize(structure))`

---

## 🔁 **Structural Convergence Invariant**

`arrival_structure_A != arrival_structure_B`  
`→ resolve(normalize(S_A)) = resolve(normalize(S_B))`

Provided:

• structures converge to the same set  

---

## ⚡ **Suggested 1-Minute Demo Flow**

1. Run base script  
2. Observe 3-node resolution  
3. Observe replay scenario  
4. Observe conflict → **ABSTAIN**  
5. Observe ambiguity → **ABSTAIN**  
6. Observe 5-node convergence  
7. Generate JSON output  

---

## 🧠 **What This Proves**

A decision system can:

• start with incomplete inputs  
• receive unordered signals  
• operate without clocks  
• avoid synchronization  

And still:

**arrive at the same final decision**

---

## ⭐ **One-Line Summary**

ORL-AI demonstrates that independent systems starting with incomplete and unordered inputs can converge deterministically to the same final decision — without relying on time, order, synchronization, or coordination — by resolving only structurally valid decisions while safely handling incomplete, conflicting, and ambiguous states.
