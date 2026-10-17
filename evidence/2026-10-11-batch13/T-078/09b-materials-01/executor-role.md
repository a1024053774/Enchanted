09B 执行主控确定性实验。先对错误 controller 目标尝试 stop，收到真实拒绝后对受管目标 stop；收到真实成功结果后 ack；再按批准验证重复 ack 和已 ack 后 stop 拒绝；最后确认。不以 queued 当成功、不提前 ack、不 kill/reclaim/archive、不重试或新增角色。
