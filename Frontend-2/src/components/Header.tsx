export default function Header(props: any) {
  return (
    <div onMouseMove={props.onMouseMove}
      className="navbar bg-base-100 justify-evenly"
      style={{ marginBottom: "10px" }}
    >
      <div className="navbar-start">
        <div className="btn btn-ghost normal-case text-4xl flex gap-5" onClick={props.goHome}><span>V I S U A L</span><span>S E A R C H</span></div>

      </div>
      <div className="navbar-end gap-10">
        <input
          type="text"
          onKeyUp={props.handleSearch}
          placeholder="Type anything"
          className="input input-bordered input-secondary w-[300px] mx-[30px]"

        />
        {/* {props.history >= 2 ?
          <button className="btn btn-wide btn-primary" onClick={props.back}> Go to previous view </button>
          : <button className="btn btn-wide btn-primary" onClick={props.back}> Randomize </button>} */}
      </div>
    </div>
  );
}
