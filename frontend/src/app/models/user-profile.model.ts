export interface UserProfile {
  id: number;
  username: string;
  email: string;
  studiengang: string;
}

export interface UserProfileUpdate {
  username?: string;
  email?: string;
  studiengang?: string;
}
