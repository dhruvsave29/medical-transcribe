import { useSessionStore } from '../store/sessionStore'
import { buildPrescriptionText } from '../lib/prescription'
import { emptySummary, type ClinicalSummary } from '../types/clinical'
import { Icon, type IconName } from './Icon'

import type { JSX } from 'react'

function Empty({ label }: { label: string }) {
  return <p className="empty">{label}</p>
}

function BulletList({ items, neg = false }: { items: string[]; neg?: boolean }) {
  return (
    <ul className="list-unstyled">
      {items.map((item, i) => (
        <li key={i} className={neg ? 'neg' : undefined}>
          {item}
        </li>
      ))}
    </ul>
  )
}

type SectionRow = { label: string; icon: IconName; content: JSX.Element }

function buildSections(summary: ClinicalSummary, displayedSummaryText: string): SectionRow[] {
  const {
    patient: _patient,
    chief_complaints,
    history_of_present_illness: hpi,
    symptoms,
    past_medical_history: pmh,
    medications,
    allergies,
    clinical_observations,
    assessment,
    plan,
  } = summary
  void _patient

  const sections: SectionRow[] = [
    {
      label: 'Clinical Summary',
      icon: 'clipboard',
      content: (
        <textarea
          key="cs"
          className="summary-textarea"
          placeholder="AI-generated clinical summary will appear here…"
          value={displayedSummaryText}
          onChange={(e) => useSessionStore.getState().setEditedSummary(e.target.value)}
          aria-label="Editable clinical summary"
        />
      ),
    },
    {
      label: 'Chief Complaints',
      icon: 'complaint',
      content:
        chief_complaints.length ? (
          <BulletList items={chief_complaints} />
        ) : (
          <Empty label="No complaints extracted yet" />
        ),
    },
    {
      label: 'Symptoms',
      icon: 'thermometer',
      content:
        symptoms.positive.length || symptoms.negative.length ? (
          <>
            {symptoms.positive.length > 0 && (
              <>
                <p className="sub-label">Reported</p>
                <BulletList items={symptoms.positive} />
              </>
            )}
            {symptoms.negative.length > 0 && (
              <>
                <p className="sub-label">Denied by patient</p>
                <BulletList items={symptoms.negative} neg />
              </>
            )}
          </>
        ) : (
          <Empty label="No symptoms extracted yet" />
        ),
    },
    {
      label: 'Clinical Impression',
      icon: 'bulb',
      content:
        assessment.provisional_diagnosis || assessment.differentials.length ? (
          <>
            {assessment.provisional_diagnosis && (
              <BulletList items={[assessment.provisional_diagnosis]} />
            )}
            {assessment.differentials.length > 0 && (
              <>
                <p className="sub-label">Differentials</p>
                <BulletList items={assessment.differentials} neg />
              </>
            )}
          </>
        ) : (
          <Empty label="No diagnosis inferred" />
        ),
    },
    {
      label: 'Medications',
      icon: 'pill',
      content:
        medications.length ? (
          <ul className="list-unstyled">
            {medications.map((m, i) => (
              <li key={i}>
                <span className="med-row">
                  <span className="med-name">{m.name}</span>
                  {m.dosage && <span className="med-dosage">{m.dosage}</span>}
                  {m.adherence && <span className="med-chip">{m.adherence}</span>}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <Empty label="No medications extracted yet" />
        ),
    },
    {
      label: 'Examinations & Tests',
      icon: 'flask',
      content:
        clinical_observations.vitals.length ||
        clinical_observations.examination_findings.length ||
        plan.investigations.length ? (
          <>
            {clinical_observations.vitals.length > 0 && (
              <>
                <p className="sub-label">Vitals</p>
                <BulletList items={clinical_observations.vitals} />
              </>
            )}
            {clinical_observations.examination_findings.length > 0 && (
              <>
                <p className="sub-label">Findings</p>
                <BulletList items={clinical_observations.examination_findings} />
              </>
            )}
            {plan.investigations.length > 0 && (
              <>
                <p className="sub-label">Ordered</p>
                <BulletList items={plan.investigations} />
              </>
            )}
          </>
        ) : (
          <Empty label="No examinations extracted yet" />
        ),
    },
    {
      label: 'Allergies',
      icon: 'alert',
      content:
        allergies.length ? (
          <BulletList items={allergies} />
        ) : (
          <Empty label="No allergies extracted yet" />
        ),
    },
    {
      label: 'Past Medical History',
      icon: 'folder',
      content:
        pmh.conditions.length || pmh.surgeries.length || pmh.hospitalisations.length ? (
          <>
            {pmh.conditions.length > 0 && (
              <>
                <p className="sub-label">Conditions</p>
                <BulletList items={pmh.conditions} />
              </>
            )}
            {pmh.surgeries.length > 0 && (
              <>
                <p className="sub-label">Surgeries</p>
                <BulletList items={pmh.surgeries} />
              </>
            )}
            {pmh.hospitalisations.length > 0 && (
              <>
                <p className="sub-label">Hospitalisations</p>
                <BulletList items={pmh.hospitalisations} />
              </>
            )}
          </>
        ) : (
          <Empty label="No past medical history extracted" />
        ),
    },
    {
      label: 'History & Follow-up',
      icon: 'calendar',
      content:
        hpi.onset ||
        hpi.duration ||
        hpi.progression ||
        hpi.aggravating_factors.length > 0 ||
        hpi.relieving_factors.length > 0 ||
        plan.follow_up ? (
          <>
            <p className="sub-label">History of present illness</p>
            {hpi.onset ||
            hpi.duration ||
            hpi.progression ||
            hpi.aggravating_factors.length ||
            hpi.relieving_factors.length ? (
              <BulletList
                items={[
                  ...(hpi.onset ? [`Onset: ${hpi.onset}`] : []),
                  ...(hpi.duration ? [`Duration: ${hpi.duration}`] : []),
                  ...(hpi.progression ? [`Progression: ${hpi.progression}`] : []),
                  ...hpi.aggravating_factors.map((f) => `Aggravating: ${f}`),
                  ...hpi.relieving_factors.map((f) => `Relieving: ${f}`),
                ]}
              />
            ) : (
              <Empty label="No history of present illness extracted" />
            )}
            {plan.follow_up && (
              <>
                <p className="sub-label">Follow-up</p>
                <BulletList items={[plan.follow_up]} />
              </>
            )}
          </>
        ) : (
          <Empty label="No history or follow-up extracted yet" />
        ),
    },
  ]

  return sections
}

function Skeleton() {
  return (
    <div className="section-block">
      <div className="section-label skeleton" style={{ minHeight: 14 }} />
      <div className="skeleton" style={{ minHeight: 64 }} />
      <div className="skeleton" style={{ minHeight: 42 }} />
    </div>
  )
}

export function SummaryCard() {
  const summary = useSessionStore((s) => s.summary)
  const status = useSessionStore((s) => s.status)
  const clearSummary = useSessionStore((s) => s.clearSummary)
  const pushToast = useSessionStore((s) => s.pushToast)
  const editedText = useSessionStore((s) => s.summaryEditedText)

  const processing = status === 'processing' && !summary
  const active = summary ?? emptySummary()
  const displayedSummaryText = editedText ?? summary?.clinical_summary ?? ''

  const patient = summary?.patient
  const metaBits = [
    patient?.age ? `Age: ${patient.age}` : 'Age: —',
    patient?.sex ? `Gender: ${patient.sex}` : 'Gender: —',
  ]

  const onCopy = async () => {
    if (!summary) {
      pushToast('info', 'Nothing to copy yet — process a transcript first.')
      return
    }
    const text = buildPrescriptionText(summary, editedText)
    try {
      await navigator.clipboard.writeText(text)
      pushToast('success', 'Copied.')
    } catch {
      pushToast('error', 'Clipboard write failed — copy manually from the clinical summary.')
    }
  }

  const onClear = () => {
    if (!summary && !processing) return
    clearSummary()
    pushToast('success', 'Summary cleared.')
  }

  return (
    <section className="card summary-card" aria-labelledby="summary-title">
      <div className="card__title">
        <Icon name="hourglass" size={22} />
        <h2 id="summary-title">AI Medical Summary</h2>
        <span className="spacer" />
        <button type="button" className="clear-x" onClick={onClear} aria-label="Clear summary">
          <Icon name="x" size={13} />
          Clear
        </button>
      </div>

      <div className="patient-header">
        <span className={`patient-name${patient?.name ? '' : ' is-unknown'}`}>
          Patient Name: {patient?.name ?? 'Not identified yet'}
        </span>
        <span className="patient-meta">{metaBits.join(' · ')}</span>
      </div>

      <div className="summary-body">
        {processing ? (
          <>
            <Skeleton />
            <Skeleton />
          </>
        ) : (
          buildSections(active, displayedSummaryText).map((row) => (
            <SummarySectionBlockTwo key={row.label} row={row} />
          ))
        )}
      </div>

      <div className="summary-footer">
        <button
          type="button"
          className="btn btn--primary btn--block"
          onClick={() => void onCopy()}
          disabled={!summary}
          aria-label="Copy summary to prescription"
        >
          <Icon name="copy" size={16} className="btn__icon" />
          Copy to Prescription
        </button>
      </div>
    </section>
  )
}

function SummarySectionBlockTwo({ row }: { row: SectionRow }): JSX.Element {
  return (
    <div className="section-block">
      <div className="section-label">
        <Icon name={row.icon} size={13} />
        {row.label}
      </div>
      {row.content}
    </div>
  )
}
