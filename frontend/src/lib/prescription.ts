/**
 * Builds the clean, ordered plain-text block copied by
 * "Copy to Prescription" (PRD Section 3: patient line, summary, complaints,
 * symptoms, impression, medications, tests, allergies, history, follow-up).
 *
 * Sections the transcript did not cover are omitted, not invented.
 */

import type { ClinicalSummary } from '../types/clinical'

const dash = ' — '

function bulletList(items: string[], prefix = ''): string[] {
  return items.map((i) => `${prefix}• ${i}`)
}

export function buildPrescriptionText(
  summary: ClinicalSummary,
  editedClinicalSummary?: string | null,
): string {
  const lines: string[] = []
  const { patient } = summary

  lines.push(
    `PATIENT: ${patient.name ?? '[name not identified]'}`,
    `AGE/SEX: ${patient.age ?? '[not given]'} / ${patient.sex ?? '[not given]'}` +
      (patient.identifiers.length ? `   ID: ${patient.identifiers.join(', ')}` : ''),
  )

  lines.push('')
  lines.push('CLINICAL SUMMARY')
  lines.push(editedClinicalSummary ?? summary.clinical_summary ?? '[no summary]')

  if (summary.chief_complaints.length) {
    lines.push('', 'CHIEF COMPLAINTS', ...bulletList(summary.chief_complaints))
  }

  if (summary.symptoms.positive.length || summary.symptoms.negative.length) {
    lines.push('', 'SYMPTOMS')
    if (summary.symptoms.positive.length) {
      lines.push(...bulletList(summary.symptoms.positive))
    }
    if (summary.symptoms.negative.length) {
      lines.push(...bulletList(summary.symptoms.negative, 'Negated: '))
    }
  }

  const { assessment } = summary
  if (assessment.provisional_diagnosis || assessment.differentials.length) {
    lines.push('', 'CLINICAL IMPRESSION')
    if (assessment.provisional_diagnosis) {
      lines.push(`• Provisional diagnosis: ${assessment.provisional_diagnosis}`)
    }
    if (assessment.differentials.length) {
      lines.push(...bulletList(assessment.differentials, 'Differential: '))
    }
  }

  if (summary.medications.length) {
    lines.push('', 'MEDICATIONS')
    for (const m of summary.medications) {
      const parts = [m.name]
      if (m.dosage) parts.push(m.dosage)
      if (m.adherence) parts.push(`(adherence: ${m.adherence})`)
      lines.push(`• ${parts.join(dash)}`)
    }
  }

  const { clinical_observations, plan } = summary
  if (
    clinical_observations.vitals.length ||
    clinical_observations.examination_findings.length ||
    plan.investigations.length
  ) {
    lines.push('', 'EXAMINATIONS & TESTS')
    if (clinical_observations.vitals.length) {
      lines.push(...bulletList(clinical_observations.vitals, 'Vitals: '))
    }
    if (clinical_observations.examination_findings.length) {
      lines.push(...bulletList(clinical_observations.examination_findings, 'Finding: '))
    }
    if (plan.investigations.length) {
      lines.push(...bulletList(plan.investigations, 'Ordered: '))
    }
  }

  if (summary.allergies.length) {
    lines.push('', 'ALLERGIES', ...bulletList(summary.allergies))
  }

  const { past_medical_history: pmh, history_of_present_illness: hpi } = summary
  if (pmh.conditions.length || pmh.surgeries.length || pmh.hospitalisations.length) {
    lines.push('', 'PAST MEDICAL HISTORY')
    if (pmh.conditions.length) lines.push(...bulletList(pmh.conditions, 'Conditions: '))
    if (pmh.surgeries.length) lines.push(...bulletList(pmh.surgeries, 'Surgeries: '))
    if (pmh.hospitalisations.length) {
      lines.push(...bulletList(pmh.hospitalisations, 'Hospitalisations: '))
    }
  }

  if (hpi.onset) lines.push('', 'HISTORY OF PRESENT ILLNESS')
  if (hpi.onset) lines.push(`• Onset: ${hpi.onset}`)
  if (hpi.duration) lines.push(`• Duration: ${hpi.duration}`)
  if (hpi.progression) lines.push(`• Progression: ${hpi.progression}`)
  if (hpi.aggravating_factors.length) {
    lines.push(...bulletList(hpi.aggravating_factors, 'Aggravating: '))
  }
  if (hpi.relieving_factors.length) {
    lines.push(...bulletList(hpi.relieving_factors, 'Relieving: '))
  }

  if (plan.follow_up) lines.push('', 'FOLLOW-UP', `• ${plan.follow_up}`)

  if (plan.advice.length) lines.push('', 'ADVICE', ...bulletList(plan.advice))
  if (plan.prescriptions.length) {
    lines.push('', 'PRESCRIPTIONS', ...bulletList(plan.prescriptions))
  }

  lines.push('')
  lines.push(
    'AI-generated clinical note prepared locally by MediScript. ' +
      'Review and approve by a clinician before entering into any medical record.',
  )

  return lines.join('\n')
}
