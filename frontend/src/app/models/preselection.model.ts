export interface PreselectionData {
  semester: string;
  target_ects: number;
  preferred_days: string [];
  mandatory_courses: string;
}

export interface Weekdays {
  monday: boolean;
  tuesday: boolean;
  wednesday: boolean;
  thursday: boolean;
  friday: boolean;
  noRestriction: boolean;
}

export interface PlanningResponse {
  id: number;
  title: string;
  semester: string;
  target_ects: number;
  preferred_days: string [];
  mandatory_courses: string;
  created_at: string;
  last_modified: string;
}

export interface RecentPlanningsResponse {
  plannings: PlanningResponse[];
  total: number;
}

export interface  RAGStartResponse {
  status: string;
  message: string;
  session_id: string | null;
}
