export interface PreselectionData {
  semester: string;
  ects: number;
  selectedDays: string [];
  preferredCourses: string;
}

export interface Weekdays {
  monday: boolean;
  tuesday: boolean;
  wednesday: boolean;
  thursday: boolean;
  friday: boolean;
  noRestriction: boolean;
}
