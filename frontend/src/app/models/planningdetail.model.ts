interface LvaItem {
  name: string;
  type: string;
  ects: number;
  day: string;
  time: string;
  instructor: string;
  reason: string;
}

interface SemesterPlanJson {
  lvas: LvaItem[];
  summary: string;
  semester: string;
  uni_days: string[];
  warnings?: string;
  total_ects: number;
}
