interface StepperProps {
  currentStep: number
  steps: Array<{ number: number; title: string }>
}

export default function Stepper({ currentStep, steps }: StepperProps) {
  return (
    <div className="glass-card p-6 mb-8">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => (
          <div key={step.number} className="flex items-center flex-1">
            {/* Step circle */}
            <div className="flex flex-col items-center">
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center font-bold transition-smooth ${
                  step.number < currentStep
                    ? 'bg-green-600 text-white'
                    : step.number === currentStep
                    ? 'bg-blue-600 text-white ring-4 ring-blue-600/30'
                    : 'bg-white/10 text-white/40'
                }`}
              >
                {step.number < currentStep ? '✓' : step.number}
              </div>
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
                  step.number < currentStep ? 'bg-green-600' : 'bg-white/10'
                }`}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
