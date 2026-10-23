/**
 * ClinicalSummary contract — mirrors PRD Section 3.3 exactly.
 * The backend (Step 4) validates LLM output against the same shape with Pydantic.
 */

export interface PatientInfo {
  name: string | null
  age: string | null
  sex: string | null
  identifiers: string[]
}

export interface HistoryOfPresentIllness {
  onset: string | null
  duration: string | null
  progression: string | null
  aggravating_factors: string[]
  relieving_factors: string[]
}

export interface Symptoms {
  positive: string[]
  negative: string[]
}

export interface PastMedicalHistory {
  conditions: string[]
  surgeries: string[]
  hospitalisations: string[]
}

export interface Medication {
  name: string
  dosage: string | null
  adherence: string | null
}

export interface ClinicalObservations {
  vitals: string[]
  examination_findings: string[]
}

export interface Assessment {
  provisional_diagnosis: string | null
  differentials: string[]
}

export interface Plan {
  investigations: string[]
  prescriptions: string[]
  advice: string[]
  follow_up: string | null
}

export interface ClinicalSummary {
  patient: PatientInfo
  chief_complaints: string[]
  history_of_present_illness: HistoryOfPresentIllness
  symptoms: Symptoms
  past_medical_history: PastMedicalHistory
  medications: Medication[]
  allergies: string[]
  clinical_observations: ClinicalObservations
  assessment: Assessment
  plan: Plan
  clinical_summary: string
}

export function emptySummary(): ClinicalSummary {
  return {
    patient: { name: null, age: null, sex: null, identifiers: [] },
    chief_complaints: [],
    history_of_present_illness: {
      onset: null,
      duration: null,
      progression: null,
      aggravating_factors: [],
      relieving_factors: [],
    },
    symptoms: { positive: [], negative: [] },
    past_medical_history: { conditions: [], surgeries: [], hospitalisations: [] },
    medications: [],
    allergies: [],
    clinical_observations: { vitals: [], examination_findings: [] },
    assessment: { provisional_diagnosis: null, differentials: [] },
    plan: { investigations: [], prescriptions: [], advice: [], follow_up: null },
    clinical_summary: '',
  }
}
