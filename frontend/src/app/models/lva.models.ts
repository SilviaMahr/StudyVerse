export interface LVA {
  id: number;
  hierarchieLevel10: string;
  hierarchieLevel11: string;
  hierarchieLevel12: string;
  type: string;
  name: string;
  ects: number;
  is_completed: boolean;
}

export interface LVAModule {
  module_name: string;
  lvas: LVA[];
  total_ects: number;
}

export interface PflichtfaecherResponse {
  pflichtfaecher: LVAModule[];
}

export interface WahlfaecherResponse {
  wahlfaecher: LVAModule[];
}

export interface CompletedLVAsUpdate {
  lva_ids: number[];
}

