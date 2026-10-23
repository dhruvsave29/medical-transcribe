import type { ClinicalSummary } from '../types/clinical'

/**
 * Demo data — strictly dev-only. Lives behind the "Demo data" toggle in the
 * top bar (visible in dev builds only) so every filled state can be designed
 * and reviewed. It must never be shown as if it were real output.
 *
 * The content is a fictional sample consultation that matches
 * src/data/mockTranscript.ts one-to-one.
 */

export const mockSummary: ClinicalSummary = {
  patient: {
    name: 'Ramesh Gupta',
    age: '41',
    sex: 'male',
    identifiers: ['OPD-2291'],
  },
  chief_complaints: [
    'Heaviness in the chest while climbing stairs',
    'Palpitations at night',
  ],
  history_of_present_illness: {
    onset: 'About three months ago',
    duration: 'Present most days now',
    progression: 'Gradually worsening',
    aggravating_factors: ['Climbing stairs', 'Cold weather'],
    relieving_factors: ['Rest'],
  },
  symptoms: {
    positive: [
      'Breathlessness after fast walking',
      'Morning cough',
      'Palpitations at night, once or twice a week',
    ],
    negative: ['No chest pain at rest', 'No fever', 'No night sweats'],
  },
  past_medical_history: {
    conditions: ['Type 2 diabetes mellitus since 2018'],
    surgeries: ['Appendicectomy in 2015'],
    hospitalisations: ['One overnight stay in 2021 for dehydration'],
  },
  medications: [
    {
      name: 'Metformin',
      dosage: '500 mg twice daily',
      adherence: 'Regular',
    },
    {
      name: 'Atorvastatin',
      dosage: '10 mg at night',
      adherence: 'Stopped a week ago',
    },
  ],
  allergies: ['Penicillin — causes a rash'],
  clinical_observations: {
    vitals: ['Blood pressure 138/88 mmHg', 'Pulse 92 bpm, regular'],
    examination_findings: [
      'Chest clear on auscultation',
      'No peripheral oedema',
    ],
  },
  assessment: {
    provisional_diagnosis: 'Possible stable angina',
    differentials: ['Hypertensive heart disease', 'Anaemia-related fatigue'],
  },
  plan: {
    investigations: ['ECG', 'Treadmill stress test', 'Lipid profile', 'HbA1c'],
    prescriptions: ['Aspirin 75 mg once daily', 'Continue Metformin 500 mg twice daily'],
    advice: [
      'Reduce salt intake',
      'Walk 30 minutes daily',
      'Stop smoking',
    ],
    follow_up: 'Review in 2 weeks with all test reports',
  },
  clinical_summary:
    'A 41-year-old male with type 2 diabetes presents with a 3-month history of progressively worsening exertional chest heaviness, night-time palpitations and breathlessness on exertion. Examination is unremarkable apart from mild hypertension. Possible stable angina is suspected. Management includes a cardiac work-up (ECG, treadmill stress test, lipid profile, HbA1c), initiation of Aspirin, reinstalling the statin, and lifestyle advice, with review in 2 weeks.',
}
