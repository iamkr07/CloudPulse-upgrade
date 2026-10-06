// EC2 Instance Details and Helper Functions

export const EC2_DETAILS = {
  "t2.micro": {
    family: "Burstable General Purpose",
    description: "Low usage workloads",
    cpu: "Low",
    use_case: "Testing, idle services",
    color: "bg-gray-500/10 text-gray-400 border-gray-500/20",
    badge_color: "gray"
  },
  "t3.medium": {
    family: "General Purpose",
    description: "Balanced workloads",
    cpu: "Moderate",
    use_case: "Web apps, APIs",
    color: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    badge_color: "blue"
  },
  "c5.large": {
    family: "Compute Optimized",
    description: "CPU-heavy workloads",
    cpu: "High",
    use_case: "Processing, batch jobs",
    color: "bg-orange-500/10 text-orange-400 border-orange-500/20",
    badge_color: "orange"
  },
}

/**
 * Get recommended EC2 instance type based on CPU usage.
 */
export function getEC2Suggestion(cpu) {
  if (cpu < 20) {
    return "t2.micro"
  } else if (cpu > 70) {
    return "c5.large"
  } else {
    return "t3.medium"
  }
}

/**
 * Get explanation for why a specific EC2 instance is suggested from CPU only.
 */
export function getEC2Explanation(cpu) {
  if (cpu > 70) {
    return "CPU-intensive workload detected → compute optimized instance selected for better performance"
  } else if (cpu < 20) {
    return "Low utilization detected → burstable instance selected to minimize costs"
  } else {
    return "Moderate CPU workload → general-purpose instance selected for flexibility"
  }
}

/**
 * Format instance type for display with details
 */
export function formatInstanceType(instanceType) {
  if (!instanceType || !EC2_DETAILS[instanceType]) {
    return "t3.medium"
  }
  return instanceType
}
