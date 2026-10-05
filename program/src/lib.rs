//! GradientMine v1 wire protocol. The evaluator is trusted; this program never evaluates a model.
#![allow(deprecated, unexpected_cfgs)]
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    clock::Clock,
    entrypoint::ProgramResult,
    program::{invoke, invoke_signed},
    program_error::ProgramError,
    pubkey::Pubkey,
    rent::Rent,
    system_instruction, system_program,
    sysvar::Sysvar,
};

#[cfg(not(feature = "no-entrypoint"))]
solana_program::entrypoint!(process_instruction);

pub const BOUNTY_SIZE: usize = 232;
pub const SUBMISSION_SIZE: usize = 144;
const MAGIC: &[u8; 8] = b"GMBOUNT1";
const SUB_MAGIC: &[u8; 8] = b"GMSUBM01";
const MAX_REWARD: u64 = 1_000_000_000;
const MAX_SUBMISSIONS: u8 = 8;

#[derive(Clone, Debug, PartialEq)]
pub struct Bounty {
    pub state: u8,
    pub count: u8,
    pub creator: Pubkey,
    pub validator: Pubkey,
    pub job: [u8; 32],
    pub policy: [u8; 32],
    pub deadline: i64,
    pub refund_after: i64,
    pub reward: u64,
    pub winner: Pubkey,
    pub receipt: [u8; 32],
}

fn bad() -> ProgramError { ProgramError::InvalidArgument }
fn arr(data: &[u8], offset: usize) -> Result<[u8; 32], ProgramError> {
    data.get(offset..offset + 32).ok_or_else(bad)?.try_into().map_err(|_| bad())
}
fn i64_at(data: &[u8], offset: usize) -> Result<i64, ProgramError> {
    Ok(i64::from_le_bytes(data.get(offset..offset + 8).ok_or_else(bad)?.try_into().map_err(|_| bad())?))
}
fn u64_at(data: &[u8], offset: usize) -> Result<u64, ProgramError> {
    Ok(u64::from_le_bytes(data.get(offset..offset + 8).ok_or_else(bad)?.try_into().map_err(|_| bad())?))
}
fn require(value: bool) -> ProgramResult {
    if value { Ok(()) } else { Err(bad()) }
}
fn signer(account: &AccountInfo) -> ProgramResult {
    if account.is_signer { Ok(()) } else { Err(ProgramError::MissingRequiredSignature) }
}
fn writable(account: &AccountInfo) -> ProgramResult { require(account.is_writable) }

impl Bounty {
    pub fn decode(data: &[u8]) -> Result<Self, ProgramError> {
        require(data.len() == BOUNTY_SIZE)?;
        require(&data[..8] == MAGIC && data[8] <= 2 && data[9] <= MAX_SUBMISSIONS)?;
        require(data[10..16].iter().all(|v| *v == 0))?;
        Ok(Self {
            state: data[8], count: data[9], creator: Pubkey::new_from_array(arr(data, 16)?),
            validator: Pubkey::new_from_array(arr(data, 48)?), job: arr(data, 80)?, policy: arr(data, 112)?,
            deadline: i64_at(data, 144)?, refund_after: i64_at(data, 152)?, reward: u64_at(data, 160)?,
            winner: Pubkey::new_from_array(arr(data, 168)?), receipt: arr(data, 200)?,
        })
    }
    pub fn encode(&self, data: &mut [u8]) -> ProgramResult {
        require(data.len() == BOUNTY_SIZE)?;
        data.fill(0);
        data[..8].copy_from_slice(MAGIC);
        data[8] = self.state;
        data[9] = self.count;
        data[16..48].copy_from_slice(self.creator.as_ref());
        data[48..80].copy_from_slice(self.validator.as_ref());
        data[80..112].copy_from_slice(&self.job);
        data[112..144].copy_from_slice(&self.policy);
        data[144..152].copy_from_slice(&self.deadline.to_le_bytes());
        data[152..160].copy_from_slice(&self.refund_after.to_le_bytes());
        data[160..168].copy_from_slice(&self.reward.to_le_bytes());
        data[168..200].copy_from_slice(self.winner.as_ref());
        data[200..232].copy_from_slice(&self.receipt);
        Ok(())
    }
    pub fn can_settle(&self, now: i64, validator: &Pubkey) -> ProgramResult {
        require(self.state == 0 && self.validator == *validator && now >= self.deadline && now < self.refund_after)
    }
    pub fn can_refund(&self, now: i64, creator: &Pubkey) -> ProgramResult {
        require(self.state == 0 && self.creator == *creator && now >= self.refund_after)
    }
}

pub fn validate_terms(now: i64, deadline: i64, refund_after: i64, reward: u64) -> ProgramResult {
    require(deadline > now && deadline <= now.checked_add(86400).ok_or_else(bad)?)?;
    require(refund_after == deadline.checked_add(3600).ok_or_else(bad)?)?;
    require((1_000_000..=MAX_REWARD).contains(&reward))
}

fn load_bounty(program: &Pubkey, account: &AccountInfo) -> Result<Bounty, ProgramError> {
    require(account.owner == program)?;
    let bounty = Bounty::decode(&account.try_borrow_data()?)?;
    let expected = Pubkey::find_program_address(&[b"bounty", bounty.creator.as_ref(), &bounty.job], program).0;
    require(expected == *account.key)?;
    Ok(bounty)
}

fn allocate_pda<'a>(program: &Pubkey, payer: &AccountInfo<'a>, account: &AccountInfo<'a>,
                    system: &AccountInfo<'a>, seeds: &[&[u8]], size: usize, extra: u64) -> ProgramResult {
    signer(payer)?;
    writable(payer)?;
    writable(account)?;
    require(*system.key == system_program::id())?;
    require(account.owner == &system_program::id() && account.data_is_empty())?;
    let required = Rent::get()?.minimum_balance(size).checked_add(extra).ok_or_else(bad)?;
    // An unsolicited pre-funding transfer must not permanently block a valid PDA's creation.
    if account.lamports() == 0 {
        invoke_signed(&system_instruction::create_account(payer.key, account.key, required, size as u64, program),
                      &[payer.clone(), account.clone(), system.clone()], &[seeds])?;
    } else {
        let missing = required.saturating_sub(account.lamports());
        if missing > 0 {
            invoke(&system_instruction::transfer(payer.key, account.key, missing),
                   &[payer.clone(), account.clone(), system.clone()])?;
        }
        invoke_signed(&system_instruction::allocate(account.key, size as u64),
                      &[account.clone(), system.clone()], &[seeds])?;
        invoke_signed(&system_instruction::assign(account.key, program),
                      &[account.clone(), system.clone()], &[seeds])?;
    }
    Ok(())
}

fn pay(from: &AccountInfo, to: &AccountInfo, reward: u64) -> ProgramResult {
    writable(from)?;
    writable(to)?;
    require(from.key != to.key)?;
    let remaining = from.lamports().checked_sub(reward).ok_or(ProgramError::InsufficientFunds)?;
    require(remaining >= Rent::get()?.minimum_balance(from.data_len()))?;
    let received = to.lamports().checked_add(reward).ok_or_else(bad)?;
    **from.try_borrow_mut_lamports()? = remaining;
    **to.try_borrow_mut_lamports()? = received;
    Ok(())
}

pub fn process_instruction(program: &Pubkey, accounts: &[AccountInfo], data: &[u8]) -> ProgramResult {
    let mut iter = accounts.iter();
    match data.first().copied() {
        Some(0) => {
            require(data.len() == 121 && accounts.len() == 3)?;
            let creator = next_account_info(&mut iter)?;
            let account = next_account_info(&mut iter)?;
            let system = next_account_info(&mut iter)?;
            signer(creator)?;
            let job = arr(data, 1)?;
            let policy = arr(data, 33)?;
            let validator = Pubkey::new_from_array(arr(data, 65)?);
            let deadline = i64_at(data, 97)?;
            let refund_after = i64_at(data, 105)?;
            let reward = u64_at(data, 113)?;
            require(job != [0; 32] && policy != [0; 32] && validator != Pubkey::default())?;
            validate_terms(Clock::get()?.unix_timestamp, deadline, refund_after, reward)?;
            let (expected, bump) = Pubkey::find_program_address(&[b"bounty", creator.key.as_ref(), &job], program);
            require(expected == *account.key)?;
            allocate_pda(program, creator, account, system, &[b"bounty", creator.key.as_ref(), &job, &[bump]], BOUNTY_SIZE, reward)?;
            Bounty { state: 0, count: 0, creator: *creator.key, validator, job, policy, deadline, refund_after,
                     reward, winner: Pubkey::default(), receipt: [0; 32] }.encode(&mut account.try_borrow_mut_data()?)
        }
        Some(1) => {
            require(data.len() == 65 && accounts.len() == 4)?;
            let worker = next_account_info(&mut iter)?;
            let account = next_account_info(&mut iter)?;
            let submission = next_account_info(&mut iter)?;
            let system = next_account_info(&mut iter)?;
            signer(worker)?;
            writable(account)?;
            let mut bounty = load_bounty(program, account)?;
            let now = Clock::get()?.unix_timestamp;
            require(bounty.state == 0 && now < bounty.deadline && bounty.count < MAX_SUBMISSIONS)?;
            require(arr(data, 1)? != [0; 32] && arr(data, 33)? != [0; 32])?;
            let (expected, bump) = Pubkey::find_program_address(&[b"submission", account.key.as_ref(), worker.key.as_ref()], program);
            require(expected == *submission.key)?;
            allocate_pda(program, worker, submission, system,
                         &[b"submission", account.key.as_ref(), worker.key.as_ref(), &[bump]], SUBMISSION_SIZE, 0)?;
            let mut bytes = submission.try_borrow_mut_data()?;
            bytes[..8].copy_from_slice(SUB_MAGIC);
            bytes[8..40].copy_from_slice(account.key.as_ref());
            bytes[40..72].copy_from_slice(worker.key.as_ref());
            bytes[72..104].copy_from_slice(&data[1..33]);
            bytes[104..136].copy_from_slice(&data[33..65]);
            bytes[136..144].copy_from_slice(&now.to_le_bytes());
            bounty.count = bounty.count.checked_add(1).ok_or_else(bad)?;
            bounty.encode(&mut account.try_borrow_mut_data()?)
        }
        Some(2) => {
            require(data.len() == 65 && accounts.len() == 4)?;
            let validator = next_account_info(&mut iter)?;
            let account = next_account_info(&mut iter)?;
            let worker = next_account_info(&mut iter)?;
            let submission = next_account_info(&mut iter)?;
            signer(validator)?;
            let mut bounty = load_bounty(program, account)?;
            bounty.can_settle(Clock::get()?.unix_timestamp, validator.key)?;
            require(submission.owner == program)?;
            let expected = Pubkey::find_program_address(&[b"submission", account.key.as_ref(), worker.key.as_ref()], program).0;
            require(expected == *submission.key)?;
            let bytes = submission.try_borrow_data()?;
            require(bytes.len() == SUBMISSION_SIZE && &bytes[..8] == SUB_MAGIC)?;
            require(&bytes[8..40] == account.key.as_ref() && &bytes[40..72] == worker.key.as_ref())?;
            require(bytes[72..104] == data[1..33] && i64_at(&bytes, 136)? < bounty.deadline)?;
            let receipt = arr(data, 33)?;
            require(receipt != [0; 32])?;
            bounty.state = 1;
            bounty.winner = *worker.key;
            bounty.receipt = receipt;
            bounty.encode(&mut account.try_borrow_mut_data()?)?;
            pay(account, worker, bounty.reward)
        }
        Some(3) => {
            require(data.len() == 1 && accounts.len() == 2)?;
            let creator = next_account_info(&mut iter)?;
            let account = next_account_info(&mut iter)?;
            signer(creator)?;
            let mut bounty = load_bounty(program, account)?;
            bounty.can_refund(Clock::get()?.unix_timestamp, creator.key)?;
            bounty.state = 2;
            bounty.encode(&mut account.try_borrow_mut_data()?)?;
            pay(account, creator, bounty.reward)
        }
        _ => Err(ProgramError::InvalidInstructionData),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn bounty() -> Bounty {
        Bounty { state: 0, count: 0, creator: Pubkey::new_unique(), validator: Pubkey::new_unique(),
                 job: [3; 32], policy: [4; 32], deadline: 2000, refund_after: 5600, reward: 1_000_000,
                 winner: Pubkey::default(), receipt: [0; 32] }
    }
    #[test]
    fn encoding_round_trip_and_malformed_data() {
        let value = bounty();
        let mut bytes = [0; BOUNTY_SIZE];
        value.encode(&mut bytes).unwrap();
        assert_eq!(Bounty::decode(&bytes).unwrap(), value);
        assert!(Bounty::decode(&bytes[..30]).is_err());
        bytes[8] = 8;
        assert!(Bounty::decode(&bytes).is_err());
    }
    #[test]
    fn only_named_validator_inside_exclusive_window() {
        let value = bounty();
        assert!(value.can_settle(2000, &value.validator).is_ok());
        assert!(value.can_settle(1999, &value.validator).is_err());
        assert!(value.can_settle(5600, &value.validator).is_err());
        assert!(value.can_settle(2000, &value.creator).is_err());
    }
    #[test]
    fn refund_only_owner_at_timeout() {
        let value = bounty();
        assert!(value.can_refund(5600, &value.creator).is_ok());
        assert!(value.can_refund(5599, &value.creator).is_err());
        assert!(value.can_refund(5600, &value.validator).is_err());
    }
    #[test]
    fn terminal_states_prevent_double_payment() {
        for state in [1, 2] {
            let mut value = bounty();
            value.state = state;
            assert!(value.can_settle(2000, &value.validator).is_err());
            assert!(value.can_refund(6000, &value.creator).is_err());
        }
    }
    #[test]
    fn strict_funding_terms_and_overflow() {
        assert!(validate_terms(1000, 2000, 5600, 1_000_000).is_ok());
        for amount in [0, 999_999, MAX_REWARD + 1, u64::MAX] {
            assert!(validate_terms(1000, 2000, 5600, amount).is_err());
        }
        assert!(validate_terms(1000, 2000, 5599, 1_000_000).is_err());
        assert!(validate_terms(i64::MAX - 1, i64::MAX, i64::MAX, 1_000_000).is_err());
    }
    #[test]
    fn unknown_or_short_instructions_fail_without_accounts() {
        let id = Pubkey::new_unique();
        for bytes in [&[][..], &[8][..], &[0][..], &[1][..], &[2][..], &[3][..]] {
            assert!(process_instruction(&id, &[], bytes).is_err());
        }
    }
}
