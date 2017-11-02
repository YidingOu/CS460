package raft

//
// this is an outline of the API that raft must expose to
// the service (or tester). see comments below for
// each of these functions for more details.
//
// rf = Make(...)
//   create a new Raft server.
// rf.Start(command interface{}) (index, term, isleader)
//   start agreement on a new log entry
// rf.GetState() (term, isLeader)
//   ask a Raft for its current term, and whether it thinks it is leader
// ApplyMsg
//   each time a new entry is committed to the log, each Raft peer
//   should send an ApplyMsg to the service (or tester)
//   in the same server.
//

import "sync"
import "labrpc"
import "time"
import "math/rand"
import "fmt"
import "bytes"
import "encoding/gob"


//
// as each Raft peer becomes aware that successive log entries are
// committed, the peer should send an ApplyMsg to the service (or
// tester) on the same server, via the applyCh passed to Make().
//
type ApplyMsg struct {
	Index       int
	Command     interface{}
	UseSnapshot bool   // ignore for lab2; only used in lab3
	Snapshot    []byte // ignore for lab2; only used in lab3
}

//
// A Go object implementing a single Raft peer.
//
type LogEntry struct{
	Command interface{}
	Index int
	Term int
}


const Follower = 0
const Candidate = 1
const Leader = 2


type Raft struct {
	mu        sync.Mutex          // Lock to protect shared access to this peer's state
	peers     []*labrpc.ClientEnd // RPC end points of all peers
	persister *Persister          // Object to hold this peer's persisted state
	me        int                 // this peer's index into peers[]

	currentTerm int
	votedFor int
	log []LogEntry

	commitIndex int
	lastApplied int

	nextIndex []int
	matchIndex []int
	role int

	Heartbeat chan bool
	GrantVote chan bool
	roleChan chan int
	applyCh chan ApplyMsg
	leader int
	App []chan bool
	// Your data here (2A, 2B, 2C).
	// Look at the paper's Figure 2 for a description of what
	// state a Raft server must maintain.

}

// return currentTerm and whether this server
// believes it is the leader.
func (rf *Raft) GetState() (int, bool) {


	// Your code here (2A).
	return rf.currentTerm, rf.role == 2
}

//
// save Raft's persistent state to stable storage,
// where it can later be retrieved after a crash and restart.
// see paper's Figure 2 for a description of what should be persistent.
//
func (rf *Raft) persist() {
	// Your code here (2C).
	// Example:
	 w := new(bytes.Buffer)
	 e := gob.NewEncoder(w)
	 e.Encode(rf.currentTerm)
	 e.Encode(rf.votedFor)
	 e.Encode(rf.log)
	 data := w.Bytes()
	 rf.persister.SaveRaftState(data)
}

//
// restore previously persisted state.
//
func (rf *Raft) readPersist(data []byte) {
	// Your code here (2C).
	// Example:
	rf.mu.Lock()
	defer rf.mu.Unlock()
	r := bytes.NewBuffer(data)
	d := gob.NewDecoder(r)
	d.Decode(&rf.currentTerm)
	d.Decode(&rf.votedFor)
	d.Decode(&rf.log)
	if data == nil || len(data) < 1 { // bootstrap without any state?
		return
	}
}




//
// example RequestVote RPC arguments structure.
// field names must start with capital letters!
//
type RequestVoteArgs struct {
	// Your data here (2A, 2B).
	Term int
	CandidateId int
	LastLogIndex int
	LastLogTerm int
}

//
// example RequestVote RPC reply structure.
// field names must start with capital letters!
//
type RequestVoteReply struct {
	// Your data here (2A).
	Term int
	VoteGranted bool
}


//AppendEntry Structure
type AppendEntriesArgs struct{
	Term int
	LeaderId int
	PrevLogIndex int
	PrevLogTerm int
	Entries []LogEntry
	LeaderCommit int
}

type AppendEntriesReply struct {
	Term int
	Success bool
	Nextindex int
}

//
// example RequestVote RPC handler.
//
func (rf *Raft) RequestVote(args *RequestVoteArgs, reply *RequestVoteReply) {
	// Your code here (2A, 2B).
	rf.mu.Lock()
	defer rf.mu.Unlock()
	defer rf.persist()
	if args.Term < rf.currentTerm {
			reply.Term = rf.currentTerm
			reply.VoteGranted = false
			return
		}
	if args.Term > rf.currentTerm{
		rf.currentTerm = args.Term
		rf.votedFor = -1
		rf.role = 0
		rf.roleChan <- 0
		}
	reply.Term = args.Term
	fmt.Printf("LastLogTerm:%v rf.log:%v sever:%v \n", args.LastLogTerm, rf.log[len(rf.log)-1].Term, rf.me)
	if rf.votedFor != -1 && rf.votedFor != args.CandidateId {
	    reply.VoteGranted = false  
	  }else if  rf.log[len(rf.log)-1].Term > args.LastLogTerm{
	  	reply.VoteGranted = false
	  }else if rf.log[len(rf.log)-1].Index > args.LastLogIndex && rf.log[len(rf.log)-1].Term == args.LastLogTerm{
	  	reply.VoteGranted = false
	  }else{
	    fmt.Printf("Server %v vote for server %v \n", rf.me, args.CandidateId)
	    reply.VoteGranted = true
	    rf.votedFor = args.CandidateId
	    rf.GrantVote <- true
	  }

	}


//
// example code to send a RequestVote RPC to a server.
// server is the index of the target server in rf.peers[].
// expects RPC arguments in args.
// fills in *reply with RPC reply, so caller should
// pass &reply.
// the types of the args and reply passed to Call() must be
// the same as the types of the arguments declared in the
// handler function (including whether they are pointers).
//
// The labrpc package simulates a lossy network, in which servers
// may be unreachable, and in which requests and replies may be lost.
// Call() sends a request and waits for a reply. If a reply arrives
// within a timeout interval, Call() returns true; otherwise
// Call() returns false. Thus Call() may not return for a while.
// A false return can be caused by a dead server, a live server that
// can't be reached, a lost request, or a lost reply.
//
// Call() is guaranteed to return (perhaps after a delay) *except* if the
// handler function on the server side does not return.  Thus there
// is no need to implement your own timeouts around Call().
//
// look at the comments in ../labrpc/labrpc.go for more details.
//
// if you're having trouble getting RPC to work, check that you've
// capitalized all field names in structs passed over RPC, and
// that the caller passes the address of the reply struct with &, not
// the struct itself.
//
func (rf *Raft) sendRequestVote(server int, args *RequestVoteArgs, reply *RequestVoteReply) bool {
	ok := rf.peers[server].Call("Raft.RequestVote", args, reply)
	return ok
}







func (rf *Raft) sendAppendEntries(server int, args AppendEntriesArgs, reply *AppendEntriesReply) bool{
	var n bool
	i := make(chan bool)
	go func() {
		ok := rf.peers[server].Call("Raft.AppendEntries", args, reply)
		//fmt.Printf("sendAppendEntries, replyind: %v reply.term: %v \n", reply.Nextindex, reply.Term)
		if ok == true{
			i <- ok
		}
	}()
	select {
	case <-time.After(100*time.Millisecond):
		n = false
	case n = <- i:
	}
	return n
}

func (rf *Raft) doAppendEntries(server int){
	

		rf.mu.Lock()
			//fmt.Printf("c matchIndex: %v nextIndex: %v \n", rf.matchIndex[server],rf.nextIndex[server])
            var args AppendEntriesArgs
            args.Term = rf.currentTerm
            args.LeaderId = rf.me
            args.PrevLogIndex = rf.nextIndex[server] - 1
            //fmt.Printf("rf.nextIndex[server]: %v nextIndex: %v server: %v args.PrevLogIndex:%v \n", rf.nextIndex[server], rf.nextIndex, server, args.PrevLogIndex)
            fmt.Printf("server:%v \n",server)
            //fmt.Printf("prev: %v nextIndex: %v \n",args.PrevLogIndex,  rf.nextIndex[server])
            args.PrevLogTerm = rf.log[args.PrevLogIndex - rf.log[0].Index].Term
            args.LeaderCommit = rf.commitIndex
            //fmt.Printf("LeaderCommit:%v log:%v Term:%v \n", args.LeaderCommit, rf.log, rf.currentTerm)
            if rf.nextIndex[server] < rf.log[0].Index + len(rf.log) {
                fmt.Printf("abcdefg\n")
                args.Entries = rf.log[rf.nextIndex[server] - rf.log[0].Index:]
            }
            rf.mu.Unlock()
            var reply AppendEntriesReply
            if rf.sendAppendEntries(server, args, &reply) {
            	//fmt.Printf("index:%v server: %v reply.index: %v reply.term: %v \n", rf.nextIndex[server], server, reply.Nextindex, reply.Term)
                if rf.role != 2{
					return
				}
				if args.Term != rf.currentTerm || reply.Term > args.Term{
				//fmt.Printf("a\n")	
					if reply.Term > args.Term{
						fmt.Printf("aaaa\n")	
						rf.mu.Lock()
						//rf.currentTerm = reply.Term
			            rf.votedFor = -1
			            rf.role = 0
						rf.roleChan <- 0
						rf.persist()
			            rf.mu.Unlock()
			            
					}
					return
				}
				if reply.Success == true{
					//fmt.Printf("b\n")
					rf.matchIndex[server] = reply.Nextindex - 1
					rf.nextIndex[server] = reply.Nextindex
					//fmt.Printf("AppendReply 2 , replyind: %v server: %v log: %v reply.term: %v \n", reply.Nextindex, server, rf.log[len(rf.log)-1].Index + 1, reply.Term)
					return
				}else{
					rf.nextIndex[server] = reply.Nextindex
					//fmt.Printf("c\n")
					//fmt.Printf("iiiiiiiiiiiiiiii: %v \n", rf.nextIndex[server])
				}
                return
            } else {
            	//fmt.Printf("cnm2 \n")
            }
        
    
}


func (rf *Raft) AppendEntries(args AppendEntriesArgs, reply *AppendEntriesReply){
	rf.mu.Lock()
    defer rf.mu.Unlock()
    //fmt.Printf("FollowerCommit index:%v log:%v Term: %v \n", rf.commitIndex, rf.log, rf.currentTerm)
    defer rf.persist()
   	if args.Term < rf.currentTerm {
        fmt.Printf("1\n")
        reply.Term = rf.currentTerm
        reply.Success = false
        return
  	}else{
		rf.Heartbeat <- true
	    rf.currentTerm = args.Term
	    rf.votedFor = -1
	    rf.leader = args.LeaderId
	    rf.role = 0
	    rf.roleChan <- 0
	    reply.Term = args.Term

	    if args.PrevLogIndex < rf.log[0].Index {
	    	fmt.Printf("2\n")
	        reply.Success = false
	        reply.Nextindex = rf.log[0].Index + 1
	     
	        return
	    }else if rf.log[0].Index + len(rf.log) <= args.PrevLogIndex {
	    	fmt.Printf("3\n")
	        reply.Success = false
	        reply.Nextindex = rf.log[0].Index + len(rf.log)
	        return
	    }else if rf.log[args.PrevLogIndex - rf.log[0].Index].Term != args.PrevLogTerm {
            fmt.Printf("4\n")
            reply.Success = false
            nextIndex := args.PrevLogIndex
            m := rf.log[nextIndex - rf.log[0].Index].Term
            for nextIndex >= rf.log[0].Index && rf.log[nextIndex-rf.log[0].Index].Term == m {
                nextIndex--
            }
            reply.Nextindex = nextIndex + 1
            return
        }

		var m int
		if len(args.Entries) != 0 {
			fmt.Printf("5\n")
			//fmt.Printf("Lady gagagagagagag \n")
			for i, content := range args.Entries{ 
	            if content.Index - rf.log[0].Index < len(rf.log) {
	                if content.Index - rf.log[0].Index < rf.log[0].Index || content.Index - rf.log[0].Index > rf.log[len(rf.log)-1].Index {
	                  //  fmt.Printf("nnnnnnnnnnnnnnn \n")
	                }
	                if content.Term != rf.log[content.Index - rf.log[0].Index].Term {
	                    
	                    rf.log = append(rf.log[:content.Index - rf.log[0].Index], content)
	                }
	            } else {
	                
	                rf.log = append(rf.log, args.Entries[i:]...)
	                break
	            }
	        }
			//fmt.Printf("nnnnnnnnnnnnnnnwwwwwwwwwww \n")

			reply.Nextindex = rf.log[len(rf.log)-1].Index + 1
			m = reply.Nextindex - 1
			//fmt.Printf("AppendEntries 1: %v  PrevLogIndex: %v m: %v \n", reply.Nextindex, args.PrevLogIndex, m)
		}else{
			fmt.Printf("6\n")
			reply.Nextindex = args.PrevLogIndex + 1
			m = args.PrevLogIndex 
			//fmt.Printf("m replyii: %v  PrevLogIndex: %v \n", reply.Nextindex,  args.PrevLogIndex)
		}
		reply.Success = true
		//fmt.Printf("server %v term %v role %v append success %v \n", rf.me, rf.currentTerm, rf.role, reply.Success)
		rf.FollowerCommit(args.LeaderCommit, m)
		//fmt.Printf("AppendEntries replyii: %v  PrevLogIndex: %v reply.term: %v \n", reply.Nextindex, args.PrevLogIndex, reply.Term)
		//fmt.Printf("5 lc: %v m: %v \n", args.LeaderCommit, m)
	}
}


func (rf *Raft) AppendReply(server int, args AppendEntriesArgs, reply AppendEntriesReply){
	//fmt.Printf("y, replyind: %v \n", reply.nextIndex)
	//fmt.Printf("AppendReply 1 , replyind: %v reply.Term: %v \n", reply.Nextindex, reply.Term)
	if rf.role != 2{
		return
	}
	if args.Term != rf.currentTerm || reply.Term > args.Term{
	//fmt.Printf("a\n")	
		if reply.Term > args.Term{
			fmt.Printf("aaaa\n")	
			rf.mu.Lock()
			//rf.currentTerm = reply.Term
            rf.votedFor = -1
            rf.role = 0
			rf.roleChan <- 0
            rf.mu.Unlock()
		}
		return
	}
	if reply.Success == true{
		//fmt.Printf("b\n")
		rf.matchIndex[server] = reply.Nextindex - 1
		rf.nextIndex[server] = reply.Nextindex
		//fmt.Printf("AppendReply 2 , replyind: %v server: %v log: %v reply.term: %v \n", reply.Nextindex, server, rf.log[len(rf.log)-1].Index + 1, reply.Term)
		return
	}else{
		rf.nextIndex[server] = reply.Nextindex
		//fmt.Printf("c\n")
		//fmt.Printf("iiiiiiiiiiiiiiii: %v \n", rf.nextIndex[server])
	}
}





//
// the service using Raft (e.g. a k/v server) wants to start
// agreement on the next command to be appended to Raft's log. if this
// server isn't the leader, returns false. otherwise start the
// agreement and return immediately. there is no guarantee that this
// command will ever be committed to the Raft log, since the leader
// may fail or lose an election.
//
// the first return value is the index that the command will appear at
// if it's ever committed. the second return value is the current
// term. the third return value is true if this server believes it is
// the leader.
//
func (rf *Raft) FollowerCommit(leaderCommit int, m int) {
	//fmt.Printf("hi:%v \n", p)
	p := rf.commitIndex
	if leaderCommit > rf.commitIndex {
		if leaderCommit < m {
			rf.commitIndex = leaderCommit
		} else {
			rf.commitIndex = m
		}
	}else{
		//fmt.Printf("leaderCommit:%v rf.commitIndex:%v \n", leaderCommit, rf.commitIndex)
	}
	var t int
	for p++; p <= rf.commitIndex; p++ {
		rf.applyCh <- ApplyMsg{Index:p, Command:rf.log[p-rf.log[0].Index].Command}
		t = p
	}
	rf.lastApplied = t
	//fmt.Printf("done \n")
	//fmt.Printf("server %v term %v role %v last append %v \n", rf.me, rf.currentTerm, rf.role, rf.lastApplied)
}

func (rf *Raft) LeaderCommit(){
	rf.mu.Lock()
	defer rf.mu.Unlock()
	defer rf.persist()
	a := rf.commitIndex
	b := a
	//fmt.Printf("a\n")
	for i := len(rf.log)-1; rf.log[i].Index>a && rf.log[i].Term==rf.currentTerm; i-- {
		countServer := 1
		for server := range rf.peers {
			//fmt.Printf("c matchIndex: %v base: %v \n", rf.matchIndex[server],rf.log[i].Index )
			if server != rf.me && rf.matchIndex[server] >= rf.log[i].Index {
				countServer++
			}
		}
		//fmt.Printf("c counter: %v \n", countServer)
		if countServer * 2 > len(rf.peers) {
			//fmt.Printf("coooooooooool \n")
			b = rf.log[i].Index
			break
		}
	}
	if a == b {
		//fmt.Printf("b\n")
		return
	}else{

		rf.commitIndex = b
		fmt.Printf("updateLeaderCommit:%v \n", rf.commitIndex)
		var t int
		for i := a + 1; i <= b; i++ {
			rf.applyCh <- ApplyMsg{Index:i, Command:rf.log[i-rf.log[0].Index].Command}
			t = i
		}
		rf.lastApplied = t
		//fmt.Printf("server %v term %v role %v last append %v \n", rf.me, rf.currentTerm, rf.role, rf.commitIndex)
	}
}

func (rf *Raft) Start(command interface{}) (int, int, bool) {
	index := -1
	term := -1
	isLeader := true
	n := len(rf.log)
	// Your code here (2B).
	if rf.role == 2 {
		rf.mu.Lock()
		defer rf.mu.Unlock()
		defer rf.persist()
		isLeader = true
		term = rf.currentTerm
		index = n + rf.log[0].Index
		args := LogEntry{Command:command, Term: term, Index: index}
		rf.log = append(rf.log, args)
	}else{
		isLeader = false
	}


	return index, term, isLeader
}

//
// the tester calls Kill() when a Raft instance won't
// be needed again. you are not required to do anything
// in Kill(), but it might be convenient to (for example)
// turn off debug output from this instance.
//
func (rf *Raft) Kill() {
	// Your code here, if desired.
}

//
// the service or tester wants to create a Raft server. the ports
// of all the Raft servers (including this one) are in peers[]. this
// server's port is peers[me]. all the servers' peers[] arrays
// have the same order. persister is a place for this server to
// save its persistent state, and also initially holds the most
// recent saved state, if any. applyCh is a channel on which the
// tester or service expects Raft to send ApplyMsg messages.
// Make() must return quickly, so it should start goroutines
// for any long-running work.
//
func Make(peers []*labrpc.ClientEnd, me int,
	persister *Persister, applyCh chan ApplyMsg) *Raft {
	rf := &Raft{}
	rf.peers = peers
	rf.persister = persister
	rf.me = me

	// Your initialization code here (2A, 2B, 2C).
	n := len(peers)
	
	rf.currentTerm = 0
	rf.votedFor = -1
	rf.leader = -1
	rf.role = 0
	rf.log = append(rf.log, LogEntry{Term:0, Index:0})
	rf.commitIndex = 0
	rf.lastApplied = 0
	rf.nextIndex = make([]int, n)
	rf.matchIndex = make([]int, n)
	rf.Heartbeat = make(chan bool)
	rf.GrantVote = make(chan bool)
	rf.roleChan = make(chan int)
	rf.applyCh = applyCh

	// initialize from state persisted before a crash
	rf.readPersist(persister.ReadRaftState())
	rf.randgene()
	go rf.changestatus()
	go rf.timeoutTimer()

	return rf
}
func (rf *Raft) randgene(){
	rand.Seed(time.Now().UTC().UnixNano())
}

func (rf *Raft) changestatus(){
	role := rf.role
	for true{
		switch {
		case role == 0:
			role = <-rf.roleChan
		case role == 1:
	
			go rf.startElection()
			role = <-rf.roleChan
			//fmt.Printf("Server %v change to role %v\n", rf.me, rf.role)
			
		case role == 2:
			for i := range rf.peers{
				rf.nextIndex[i] = rf.log[len(rf.log) - 1].Index + 1
				rf.matchIndex[i] = 0
				//fmt.Printf(" rf.log[len(rf.log)-1].Index: %v \n", rf.log[len(rf.log)-1].Index)
				//fmt.Printf("aaaaa")
			}
			//fmt.Printf("Server %v start to sende hb\n",rf.me)
			go rf.doHeartbeat()
			role = <-rf.roleChan
		}
	}
}
func (rf *Raft) timeoutTimer(){
	interval := int((150)*time.Millisecond)
	timeout := time.Duration(rand.Intn(interval))+(200*time.Millisecond)
	newt:= time.NewTimer(timeout)
	for {
		select{
			case <- rf.Heartbeat:
				newt.Reset(timeout)
			case <- rf.GrantVote:
				newt.Reset(timeout)
			case <- newt.C:
				rf.role = 1
				rf.roleChan <- 1
				newt.Reset(timeout)
		}
	}
}

func (rf *Raft) doHeartbeat(){
	for i := range rf.peers{
		if i == rf.me{
			go func(){
				hbtimer := time.NewTimer(100*time.Millisecond)
				for rf.role == 2{
					rf.Heartbeat <- true
					//fmt.Printf("wwwwwwwwwwww server %v term %v role %v leader hb with nextIndex %v base %v \n", rf.me, rf.currentTerm, rf.role, rf.nextIndex,rf.log[len(rf.log)-1].Index)
					rf.LeaderCommit()
					//fmt.Printf("server %v term %v role %v leader hb with nextIndex %v base %v \n", rf.me, rf.currentTerm, rf.role, rf.nextIndex,rf.log[len(rf.log)-1].Index)
					hbtimer.Reset(100*time.Millisecond)
					<-hbtimer.C
				}
			}()
		}else{
			go func(server int){
				hbtimer := time.NewTimer(100*time.Millisecond)
				for rf.role == 2{
					rf.doAppendEntries(server)
					hbtimer.Reset(100*time.Millisecond)
					<-hbtimer.C
				}
			}(i)
		}
	}
}

func (rf *Raft) startElection(){
	fmt.Printf("election strat, Server: %v \n", rf.me)
	rf.mu.Lock()
	rf.currentTerm = rf.currentTerm + 1
	rf.votedFor = rf.me
	args := new(RequestVoteArgs)
	args.Term = rf.currentTerm
	args.CandidateId = rf.me
	args.LastLogTerm = rf.log[len(rf.log)-1].Term
	args.LastLogIndex = rf.log[len(rf.log)-1].Index
	rf.persist()
	rf.mu.Unlock()
	g := len(rf.peers)
	GatherVote := make(chan bool, g)
	GatherVote <-true
	for i := range rf.peers{
		if rf.me != i{
			go func(i int){
				var reply RequestVoteReply
				if rf.sendRequestVote(i, args, &reply)==true{
					if args.Term < reply.Term{
                        rf.mu.Lock()
						rf.currentTerm = reply.Term
						rf.votedFor = -1
						rf.role = 0
						rf.roleChan <- 0
						rf.persist()
                        rf.mu.Unlock()
						return
					}else if reply.VoteGranted == true{
						//fmt.Printf("Server %v get vote from server %v", rf.me, i)
						GatherVote <- true
					}else{
						GatherVote <- false
					}
				}else{
					GatherVote <- false
				}
			}(i)
		}
	}
	rf.VotCount(GatherVote)
}
func (rf *Raft) VotCount(GatherVote chan bool){
	bol := true
	m:=0
	x:=0
	counter:=0
	n:=len(rf.peers)
	for bol{
		select{
		case ok := <- GatherVote:
			counter++
			if ok{
				//fmt.Printf("Server %v get 1 vote \n", rf.me)
				m++
			}else{
				x++
			}
			if float64(m)*float64(2) > float64(n){
				//fmt.Printf("server %v becomes leader. \n",rf.me)
				rf.role = 2
				rf.roleChan <- 2
				bol = false
			}else if float64(x)*float64(2)>float64(n){
				bol = false
			}
		}
	}
}
