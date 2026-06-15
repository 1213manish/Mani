// Core TypeScript types for the ExpenseFlow frontend

export interface User {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  full_name: string;
  is_email_verified: boolean;
  avatar_url?: string;
  bio?: string;
  phone?: string;
  date_joined: string;
}

export interface Currency {
  id: string;
  code: string;
  name: string;
  symbol: string;
  is_active: boolean;
}

export interface GroupMembership {
  id: string;
  user: User;
  role: 'ADMIN' | 'MEMBER';
  joined_at: string;
  left_at: string | null;
  is_active: boolean;
  invited_by: User | null;
  created_at: string;
}

export interface Group {
  id: string;
  name: string;
  description: string | null;
  created_by: User;
  default_currency: Currency | null;
  is_active: boolean;
  avatar_url: string | null;
  member_count: number;
  current_user_membership: GroupMembership | null;
  created_at: string;
  updated_at: string;
}

export interface ExpenseSplit {
  id: string;
  user: User;
  share_amount: string;
  share_percentage: string;
  share_units: string;
  owed_amount: string;
  is_settled: boolean;
}

export type SplitType = 'EQUAL' | 'PERCENTAGE' | 'EXACT' | 'SHARES';

export interface Expense {
  id: string;
  title: string;
  description: string | null;
  amount: string;
  currency: Currency;
  original_amount: string;
  original_currency: Currency;
  exchange_rate: string;
  converted_amount: string;
  paid_by: User;
  expense_date: string;
  group: string;
  split_type: SplitType;
  notes: string | null;
  receipt_url: string | null;
  category: string | null;
  is_deleted: boolean;
  created_by: User;
  created_at: string;
  updated_at: string;
  splits: ExpenseSplit[];
}

export interface Settlement {
  id: string;
  group: string;
  payer: User;
  receiver: User;
  amount: string;
  currency: Currency;
  settlement_date: string;
  notes: string | null;
  created_by: User;
  created_at: string;
}

// Balance types
export interface UserBalance {
  user_id: string;
  user_name: string;
  email: string;
  net_balance: string;
  status: 'creditor' | 'debtor' | 'settled';
}

export interface GroupBalances {
  group_id: string;
  group_name: string;
  balances: UserBalance[];
}

export interface SimplifiedTransaction {
  from_user_id: string;
  to_user_id: string;
  amount: string;
  from_user: { id: string; full_name: string; email: string };
  to_user: { id: string; full_name: string; email: string };
}

export interface SimplifiedSettlements {
  group_id: string;
  group_name: string;
  transactions: SimplifiedTransaction[];
  transaction_count: number;
}

export interface ExpenseBreakdown {
  expense_id: string;
  title: string;
  expense_date: string;
  total_amount: string;
  currency: string;
  paid_by?: string;
  you_paid: string;
  your_share: string;
  others_owe_you?: string;
  direction: 'YOU_PAID' | 'YOU_OWE';
}

export interface BalanceExplanation {
  user_id: string;
  user_name: string;
  net_balance: string;
  you_are_owed: string;
  you_owe: string;
  expense_breakdown: ExpenseBreakdown[];
  settlement_breakdown: any[];
  group_id: string;
  group_name: string;
}

// Import types
export type ImportStatus =
  | 'PENDING'
  | 'PARSING'
  | 'AWAITING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'COMPLETED'
  | 'FAILED';

export type AnomalyType =
  | 'DUPLICATE_EXACT'
  | 'DUPLICATE_POSSIBLE'
  | 'NEGATIVE_VALUE'
  | 'SETTLEMENT_AS_EXPENSE'
  | 'MISSING_PAYER'
  | 'INVALID_DATE'
  | 'FUTURE_DATE'
  | 'CURRENCY_MISMATCH'
  | 'UNKNOWN_MEMBER'
  | 'MEMBER_NOT_ACTIVE'
  | 'INCONSISTENT_SPLIT'
  | 'MALFORMED_ROW'
  | 'BLANK_MANDATORY_FIELD'
  | 'CONFLICTING_DUPLICATE'
  | 'AMOUNT_OUTLIER';

export type AnomalySeverity = 'ERROR' | 'WARNING' | 'INFO';
export type AnomalyStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'AUTO_RESOLVED';

export interface ImportAnomaly {
  id: string;
  row_number: number;
  raw_data: Record<string, string>;
  anomaly_type: AnomalyType;
  severity: AnomalySeverity;
  description: string;
  recommendation: string;
  action_taken: string | null;
  status: AnomalyStatus;
  resolved_by: User | null;
  resolved_at: string | null;
}

export interface ImportJob {
  id: string;
  group: string;
  uploaded_by: User;
  file_name: string;
  file_hash: string;
  status: ImportStatus;
  rows_total: number;
  rows_imported: number;
  rows_skipped: number;
  anomalies_count: number;
  error_message: string | null;
  anomaly_summary: {
    errors: number;
    warnings: number;
    info: number;
    pending: number;
  };
  created_at: string;
  completed_at: string | null;
}

// Auth types
export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Audit types
export interface AuditLog {
  id: string;
  actor: User | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  resource_repr: string | null;
  before_state: Record<string, any> | null;
  after_state: Record<string, any> | null;
  ip_address: string | null;
  extra: Record<string, any> | null;
  created_at: string;
}
