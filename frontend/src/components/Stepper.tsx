interface StepperProps {
  currentStep: number // Currently displayed step
  maxStep?: number // Maximum reached step (defaults to currentStep)
  steps: Array<{ number: number; title: string }>
  onStepClick?: (step: number) => void
}

export default function Stepper({ currentStep, maxStep, steps, onStepClick }: StepperProps) {
  const maxReachedStep = maxStep !== undefined ? maxStep : currentStep
  return (
    <div className="glass-card p-6 mb-8">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => (
          <div key={step.number} className="flex items-center flex-1">
            {/* Step circle */}
            <div className="flex flex-col items-center">
              <button
                onClick={() => onStepClick?.(step.number)}
                disabled={step.number > maxReachedStep}
                className={`w-12 h-12 rounded-full flex items-center justify-center font-bold transition-smooth ${
                  step.number < currentStep
                    ? 'bg-green-600 text-white hover:bg-green-700 cursor-pointer'
                    : step.number === currentStep
                    ? 'bg-blue-600 text-white ring-4 ring-blue-600/30 cursor-default'
                    : step.number <= maxReachedStep
                    ? 'bg-green-600 text-white hover:bg-green-700 cursor-pointer hover:scale-110'
                    : 'bg-white/10 text-white/40 cursor-not-allowed'
                } ${step.number < currentStep && step.number < maxReachedStep ? 'hover:scale-110' : ''}`}
                title={step.number <= maxReachedStep ? `Перейти к этапу ${step.number}` : 'Этап не доступен'}
              >
                {step.number < currentStep ? '✓' : step.number <= maxReachedStep ? '✓' : step.number}
              </button>
              <span
                className={`text-xs mt-2 text-center ${
                  step.number === currentStep ? 'text-white font-medium' : 'text-white/60'
                }`}
              >
                {step.title}
              </span>
            </div>

            {/* Connector line */}
            {index < steps.length - 1 && (
              <div
                className={`flex-1 h-1 mx-4 rounded transition-smooth ${
                  step.number < maxReachedStep ? 'bg-green-600' : 'bg-white/10'
                }`}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
